# PUCIT BS(CS) Academic Advisor Agent

An interactive command-line academic advising assistant for **PUCIT BS(CS)** students, built with LangChain/LangGraph and connected to a FastMCP tool server. It helps with degree and course lookups, GPA/CGPA and credit-hour calculations, multi-semester GPA target planning, saving confirmed summary reports, and keeping persistent per-student conversation threads.

---

## Features

- **Tool-backed calculations only:** All GPA, CGPA, credit-hour, and required-GPA calculations are delegated to MCP tools rather than done mentally, so every number comes directly from a tool response.
- **PUCIT special course rules:**
  - Math Deficiency courses (`MD-001`, `MD-002`) are excluded from GPA calculations as non-credit pass/fail courses.
  - Quran Translation courses (`HQ-001` through `HQ-008`, `0.5` credit hours each) are included in all calculations.
- **Automatic horizon widening for unreachable targets:** A required GPA above `4.0` in a single semester is treated as unreachable. The planner then widens the horizon across additional remaining semesters until a realistic required GPA (`<= 4.0`) is found.
- **Confirmation-gated report saving:** The agent offers to save a summary report via `save_report` only after delivering a complete calculation or advising plan (never for quick lookups), and only after explicit student confirmation.
- **Persistent SQLite memory (`AsyncSqliteSaver`):** Conversation checkpoints are stored per `thread_id` in `cgpa_memory.db`, so chat history survives CLI restarts and thread switches.
- **Real-time streaming:** Tool progress and model output are streamed using `app.astream(..., stream_mode=["updates", "messages"], version="v2")`.
- **Dangling tool call recovery:** Incomplete `tool_calls` in thread state are repaired with `repair_dangling_tool_calls` after interruptions or errors.

---

## Session Commands

| Command | Description |
|---|---|
| `/switch` | Change the active `thread_id` |
| `/history` | Inspect saved messages and tool calls |
| `/forget` | Delete saved checkpoints for the active thread |
| `exit` / `quit` | End the CLI session |

---

## Project Structure

```text
├── agent/
│   ├── main.py            # CLI entry point, streaming, SQLite checkpointer, commands, recovery
│   ├── llm.py             # LLM model configuration
│   └── requirements.txt   # Agent Python dependencies
├── server.py          # FastMCP server exposing academic advising tools (MCP server codebase (hosted separately on GitHub / cloud host)
├── tools.py           # GPA, CGPA, credit-hour, target-GPA, and report tools
└── requirements.txt   # Server Python dependencies
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- A Groq API key (`GROQ_API_KEY`)
- An MCP server URL (`MCP_URL`), either running locally at `http://127.0.0.1:8000/mcp` or pointing to a deployed server

### 1. Install dependencies

From the `agent/` directory, install with either:

```bash
cd agent
pip install -r requirements.txt
```

or install the packages directly:

```bash
pip install python-dotenv fastmcp langchain langchain-core langchain-groq langgraph-checkpoint-sqlite
```
or
```
cd agent
pip install -r requirements.txt
```

### 2. Configure environment variables

Create or update a `.env` file inside the `agent/` directory:

```env
GROQ_API_KEY=your_groq_api_key_here
MCP_URL=https://<your-hosted-server>.fastmcp.app/mcp
FASTMCP_KEY=
```

### 3. Start the MCP server (local only)

If you are running the server locally, open a terminal in the `server/` folder and run:

```bash
python server.py   # or: py server.py
```

Keep it running so it listens on `http://127.0.0.1:8000/mcp`.

> **Note:** If `MCP_URL` already points to a live hosted server, skip this step.

### 4. Start the agent

Open a second terminal in the `agent/` folder and run:

```bash
python main.py   # or: py main.py
```

### 5. Chat with the advisor

1. When prompted, enter a student name or `thread_id`. Existing saved threads are shown on startup.
2. Ask an advising, course, or GPA planning question and watch the streamed tool and advisor output.
3. Use `/history`, `/switch`, or `/forget` at any time, or type `exit` to quit.

---

## Error Handling & Recovery

- **Before each turn and on any exception**, `repair_dangling_tool_calls` inspects the active thread's state for `AIMessage` tool calls that never received a matching `ToolMessage`. It patches them with a recovery `ToolMessage` so later turns stay intact.
- **Connection drops and streaming errors** during a turn or MCP session are caught and surfaced cleanly in the CLI. You can retry, switch threads, or check the server without the program crashing.
