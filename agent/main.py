import asyncio
import os
import warnings
from pathlib import Path

from dotenv import load_dotenv
from fastmcp.client import Client
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=UserWarning)
    from langchain.mcp import MCPAdapter

from llm import llm

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SystemPrompt = """You are a helpful, encouraging academic advisor for PUCIT BS(CS) students. Communicate in a friendly, clear, and empathetic tone—like an approachable senior student or university counselor.
You must follow these strict guidelines:
1. Tool-based calculations only:
   - Do not perform mental math or calculate GPAs, grade points, or credit hours yourself.
   - All numerical values, GPAs, and credit hour totals in your responses must originate directly from tool outputs.

2. Avoid assumptions:
   - Do not guess or assume a student's marks, CGPA, semester number, or completed credit hours.
   - If required details are missing, ask the student for them directly.
   - Limit follow-up questions to 1 or 2 at a time so you don't overwhelm the student.

3. Special course handling:
   - Exclude Math Deficiency courses (MD-001, MD-002) from GPA calculations as they are non-credit pass/fail courses.
   - Include Quran Translation courses (HQ-001 through HQ-008, 0.5 credit hours each) in all calculations.

4. Unreachable targets and horizon widening:
   - A required semester GPA above 4.0 is impossible.
   - If required_gpa_for_target returns a GPA above 4.0 for a single semester, do not report that as the final answer.
   - Automatically extend the target across additional remaining semesters using get_remaining_credit_hours and required_gpa_for_target (testing 2, 3, or more semesters) until the required GPA is 4.0 or lower.
   - Present this multi-semester plan to the student as realistic guidance.

5. Report Generation Rules:
   - Only offer to save a summary report using save_report after delivering a complete calculation or advising plan.
   - Do not offer report saving for simple grade lookups or quick answers.
   - Never call save_report without explicit confirmation from the student.
"""


def _get_msg_attr(msg, key: str, default=None):
    """Safely read a field from either a LangChain message object or a dict."""
    if isinstance(msg, dict):
        return msg.get(key, default)
    return getattr(msg, key, default)


def _extract_text_from_chunk(chunk) -> str:
    """Extract plain text from message chunks, messages, or dicts."""
    if chunk is None:
        return ""
    content = _get_msg_attr(chunk, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        return "".join(parts)
    return ""


def build_mcp_target(mcp_url: str, api_key: str | None):
    """Build the MCP target for MCPAdapter (with optional FastMCP bearer auth)."""
    if api_key:
        return Client(mcp_url, auth=api_key)
    return mcp_url


async def list_threads(memory: AsyncSqliteSaver) -> list[str]:
    """Return sorted unique thread_ids saved in AsyncSqliteSaver."""
    thread_ids: set[str] = set()
    async for checkpoint_tuple in memory.alist(None):
        configurable = (checkpoint_tuple.config or {}).get("configurable", {})
        tid = configurable.get("thread_id")
        if tid:
            thread_ids.add(tid)
    return sorted(thread_ids)


async def show_history(app, thread_config: dict) -> None:
    """Print saved messages for the active thread."""
    state = await app.aget_state(thread_config)
    messages = state.values.get("messages", []) if state and state.values else []

    if not messages:
        print("\n[No saved messages in this thread.]\n")
        return

    print("\n=== Saved Chat History ===")
    for msg in messages:
        role = _get_msg_attr(msg, "type", msg.__class__.__name__)
        content = _get_msg_attr(msg, "content", "")
        tool_calls = _get_msg_attr(msg, "tool_calls", None)
        tool_call_id = _get_msg_attr(msg, "tool_call_id", None)

        if content:
            suffix = f" [tool_call_id={tool_call_id}]" if tool_call_id else ""
            print(f"[{role}{suffix}]: {content}")
        if tool_calls:
            called = [
                tc.get("name", "unknown_tool") if isinstance(tc, dict) else getattr(tc, "name", "unknown_tool")
                for tc in tool_calls
            ]
            print(f"[{role} -> tool_calls]: {', '.join(called)}")
    print("==========================\n")


async def prompt_user_name(memory: AsyncSqliteSaver, initial: bool = False) -> str:
    """Prompt for thread_id (user name), showing existing threads on startup."""
    existing = await list_threads(memory)
    if initial:
        print("Saved chat threads:", ", ".join(existing) if existing else "None yet")
    while True:
        name = (await asyncio.to_thread(input, "Who is chatting? (enter name / thread_id): ")).strip()
        if name:
            return name
        print("Please enter a non-empty name for the thread_id.")


async def repair_dangling_tool_calls(app, thread_config: dict) -> int:
    """Detect any AI tool_calls lacking a matching ToolMessage and patch thread state.

    Returns the number of dangling tool calls repaired.
    """
    state = await app.aget_state(thread_config)
    messages = state.values.get("messages", []) if state and state.values else []
    if not messages:
        return 0

    answered_ids: set[str] = set()
    for msg in messages:
        if _get_msg_attr(msg, "type") == "tool":
            tc_id = _get_msg_attr(msg, "tool_call_id")
            if tc_id:
                answered_ids.add(tc_id)

    dangling_fixes: list[ToolMessage] = []
    seen_dangling_ids: set[str] = set()

    for msg in messages:
        if _get_msg_attr(msg, "type") == "ai":
            tool_calls = _get_msg_attr(msg, "tool_calls") or []
            for tc in tool_calls:
                tc_id = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", None)
                tc_name = (
                    tc.get("name")
                    if isinstance(tc, dict)
                    else getattr(tc, "name", "unknown_tool")
                )
                if tc_id and tc_id not in answered_ids and tc_id not in seen_dangling_ids:
                    seen_dangling_ids.add(tc_id)
                    dangling_fixes.append(
                        ToolMessage(
                            content=(
                                f"[Tool '{tc_name}' did not return a response due to an "
                                "interruption or connection error.]"
                            ),
                            tool_call_id=tc_id,
                            name=tc_name,
                        )
                    )

    if dangling_fixes:
        await app.aupdate_state(thread_config, {"messages": dangling_fixes})

    return len(dangling_fixes)


async def stream_advisor_turn(app, user_input: str, thread_config: dict) -> None:
    """Stream tool/node updates and assistant tokens using v2 stream parts."""
    inputs = {"messages": [HumanMessage(content=user_input)]}
    printed_any_token = False
    announced_tools: set[str] = set()

    print("\nAdvisor: ", end="", flush=True)

    async for part in app.astream(
        inputs,
        thread_config,
        stream_mode=["updates", "messages"],
        version="v2",
    ):
        if not isinstance(part, dict):
            continue

        part_type = part.get("type")
        data = part.get("data")

        if part_type == "messages":
            # In v2 messages mode, data is typically (message_chunk, metadata)
            msg_chunk = data[0] if isinstance(data, (list, tuple)) and len(data) > 0 else data
            role = _get_msg_attr(msg_chunk, "type")
            tool_calls = _get_msg_attr(msg_chunk, "tool_calls")

            if role in {"human", "tool"}:
                continue

            if tool_calls:
                for tc in tool_calls:
                    t_name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
                    t_id = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", None)
                    key = f"{t_id or ''}:{t_name}"
                    if t_name and key not in announced_tools:
                        announced_tools.add(key)
                        print(f"\n[Calling tool: {t_name}...]\nAdvisor: ", end="", flush=True)

            text = _extract_text_from_chunk(msg_chunk)
            if text:
                print(text, end="", flush=True)
                printed_any_token = True

        elif part_type == "updates" and isinstance(data, dict):
            for _node_name, node_update in data.items():
                if not isinstance(node_update, dict):
                    continue
                for m in node_update.get("messages", []):
                    if _get_msg_attr(m, "type") == "tool":
                        tool_name = _get_msg_attr(m, "name", "tool")
                        print(f"\n[Finished tool: {tool_name}]\nAdvisor: ", end="", flush=True)

    if not printed_any_token:
        state = await app.aget_state(thread_config)
        msgs = state.values.get("messages", []) if state and state.values else []
        if msgs:
            final_text = _extract_text_from_chunk(msgs[-1])
            if final_text:
                print(final_text, end="", flush=True)

    print("\n")


async def run_chat_session(app, memory: AsyncSqliteSaver) -> None:
    """Interactive CLI loop supporting /switch, /history, /forget, streaming, and recovery."""
    name = await prompt_user_name(memory, initial=True)
    thread_config = {"configurable": {"thread_id": name}}
    print(f"\nActive thread: '{name}'. Commands: /switch, /history, /forget, exit\n")

    while True:
        user_input = (await asyncio.to_thread(input, f"[{name}] You: ")).strip()
        if not user_input:
            continue

        cmd = user_input.lower()
        if cmd in {"exit", "quit"}:
            break

        if cmd == "/switch":
            name = await prompt_user_name(memory, initial=False)
            thread_config = {"configurable": {"thread_id": name}}
            print(f"\nSwitched active thread to '{name}'.\n")
            continue

        if cmd == "/history":
            await show_history(app, thread_config)
            continue

        if cmd == "/forget":
            await memory.adelete_thread(name)
            print(f"\nForgot saved conversation for thread '{name}'.\n")
            continue

        try:
            pre_repaired = await repair_dangling_tool_calls(app, thread_config)
            if pre_repaired:
                print(
                    f"\n[Recovered {pre_repaired} dangling tool call(s) from previous interrupted turn.]\n"
                )
        except Exception as pre_exc:
            print(f"\n[Warning: pre-turn state check failed]: {pre_exc}\n")

        try:
            await stream_advisor_turn(app, user_input, thread_config)
        except Exception as exc:
            print(f"\n[Turn interrupted by error]: {exc}")
            try:
                post_repaired = await repair_dangling_tool_calls(app, thread_config)
                if post_repaired:
                    print(
                        f"[Repaired {post_repaired} dangling tool call(s) in thread '{name}'.]"
                    )
            except Exception as repair_exc:
                print(f"[Could not update thread state after error]: {repair_exc}")
            print(
                "You can retry your message, /switch threads, or ensure the MCP server is reachable.\n"
            )


async def main() -> None:
    mcp_url = os.getenv("MCP_URL", "http://127.0.0.1:8000/mcp")
    api_key = os.getenv("FASTMCP_KEY") or None
    db_path = os.getenv("SQLITE_DB_PATH", str(BASE_DIR / "cgpa_memory.db"))
    target = build_mcp_target(mcp_url, api_key)

    async with AsyncSqliteSaver.from_conn_string(db_path) as memory:
        try:
            async with MCPAdapter(target) as adapter:
                tools = await adapter.list_tools()
                app = create_agent(
                    model=llm,
                    tools=tools,
                    system_prompt=SystemPrompt,
                    checkpointer=memory,
                )
                await run_chat_session(app, memory)
        except Exception as exc:
            print(
                f"\nFailed to connect or run MCP session against '{mcp_url}': {exc}\n"
                "Check that your MCP server is running (e.g., `py server.py` on port 8000) "
                "and verify MCP_URL and FASTMCP_KEY in agent/.env.\n"
            )


if __name__ == "__main__":
    asyncio.run(main())