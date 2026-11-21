# PUCIT BS(CS) Academic Advisor Agent

An interactive command-line academic advising assistant for **PUCIT BS(CS)** students built with LangChain/LangGraph and connected to a FastMCP tool server. 
It assists students with degree and course lookups, tool-backed GPA/CGPA and credit-hour calculations, multi-semester GPA target planning, confirmed summary report saving, and persistent per-student conversation threads.

## What It Does

* **Tool-Backed Calculations Only:** Delegates all GPA, CGPA, credit-hour, and required-GPA calculations to MCP tools rather than performing mental math, ensuring numerical outputs come directly from tool responses.
* **PUCIT Special Course Rules:** Excludes Math Deficiency courses (`MD-001`, `MD-002`) from GPA calculations as non-credit pass/fail courses, while including Quran Translation courses (`HQ-001` through `HQ-008`, `0.5` credit hours each) across calculations.
* **Automatic Horizon Widening for Unreachable Targets:** Treats any single-semester required GPA above `4.0` as unreachable and automatically widens the planning horizon across additional remaining semesters until a realistic required GPA (`<= 4.0`) is found.
* **Confirmation-Gated Report Saving:** Offers to save a summary report via `save_report` only after delivering a complete calculation or advising plan—never for quick lookups—and only after explicit student confirmation.
* **Persistent SQLite Memory (`AsyncSqliteSaver`):** Persists conversation checkpoints per `thread_id` in `cgpa_memory.db` so chat history survives CLI restarts and thread switches.
* **Interactive Session Commands:** Supports `/switch` (change active `thread_id`), `/history` (inspect saved messages and tool calls), `/forget` (delete saved checkpoints for the active thread), and `exit` / `quit` (end the CLI session).
* **Real-Time Streaming & Dangling Tool Call Recovery:** Streams tool progress and model output using `app.astream(..., stream_mode=["updates", "messages"], version="v2")` and repairs incomplete `tool_calls` in thread state using `repair_dangling_tool_calls` after interruptions or errors.

## Project Structure

```text
├── agent/
│   ├── main.py          # CLI entry point, streaming, SQLite checkpointer, commands, recovery
│   ├── llm.py           # LLM model configuration
└──       
├── server.py        # FastMCP server exposing academic advising tools (# MCP server codebase (hosted separately on GitHub / cloud host)
├── tools.py         # GPA, CGPA, credit-hour, target-GPA, and report tools
└── requirements.txt # Server Python dependencies
```

## How to Run Locally
You will need Python 3.10+ available in your terminal, a Groq API key (GROQ_API_KEY), and an MCP server URL (MCP_URL)—either running locally on http://127.0.0.1:8000/mcp or pointing to a deployed server.
Inside the agent/ directory, install the required packages with:
pip install python-dotenv fastmcp langchain langchain-core langchain-groq langgraph-checkpoint-sqlite
or 
cd agent
pip install -r requirements.txt

* **Create or update .env inside the agent/ directory:**
GROQ_API_KEY=your_groq_api_key_here
MCP_URL=https://<your-hosted-server>.fastmcp.app/mcp
FASTMCP_KEY=

When running locally, start the MCP server first in a terminal inside the server/ folder (py server.py, or python server.py) and keep it running so it listens on http://127.0.0.1:8000/mcp. Then open a second terminal inside the agent/ folder and start the assistant with py main.py (or python main.py). (If MCP_URL already points to a live hosted server, you can run py main.py directly without starting a local server.py.)
Once main.py starts, enter a student name or thread_id when prompted—existing saved threads are shown on startup—then ask an advising, course, or GPA planning question and watch the streamed tool and advisor output. During a chat session, you can use /history, /switch, or /forget at any time, or type exit to quit.

* **Error Handling & Recovery Behavior:**
Before a new turn begins—and whenever a turn hits an exception—repair_dangling_tool_calls inspects the active thread's state for any AIMessage tool calls that never received a matching ToolMessage and patches them with a recovery ToolMessage so later turns stay intact. Connection drops or streaming errors during a turn or MCP session are also caught and surfaced cleanly in the CLI so you can retry, switch threads, or check the server without crashing out of the program.


