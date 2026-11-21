# PUCIT BS(CS) Academic Advisor Agent

An interactive command-line academic advising assistant for **PUCIT BS(CS)** students, built with LangChain/LangGraph and connected to a FastMCP tool server. It helps with degree and course lookups, GPA/CGPA and credit-hour calculations, multi-semester GPA target planning, saving confirmed summary reports, and keeping persistent per-student conversation threads.

**Hosted MCP server:**

```text
https://pucit-cgpa-advisor.fastmcp.app/mcp
```

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
│   ├── requirements.txt   # Agent Python dependencies
│   └── .env.example       # Example environment variables (add your own keys)
├── server.py              # FastMCP server exposing academic advising tools
├── tools.py               # GPA, CGPA, credit-hour, target-GPA, and report tools
└── requirements.txt       # Server Python dependencies
```

---

## How It Works

The project has two parts:

1. **MCP server (`server.py` + `tools.py`):** exposes the GPA, CGPA, credit-hour, target-GPA, and report tools. It is hosted at the URL above, and you can also run it locally.
2. **Agent (`agent/`):** the CLI app that runs on your own machine. It connects to an MCP server over HTTP using `MCP_URL`.

Your CLI and SQLite memory (`cgpa_memory.db`) always run on your computer. Only the tool execution happens on the MCP server, which is local or hosted depending on the method you choose.

Choose one of the two methods below.

| | Method A: Full project (local server) | Method B: Agent only (hosted server) |
|---|---|---|
| Files needed | Whole repo | `agent/` folder only |
| Server runs | On your machine | On the hosted server |
| `MCP_URL` | `http://127.0.0.1:8000/mcp` | `https://pucit-cgpa-advisor.fastmcp.app/mcp` |
| `FASTMCP_KEY` | Not needed for the local server | Required (bearer token) |
| Terminals | 2 | 1 |

---

## Prerequisites

- Python 3.10+
- A Groq API key (`GROQ_API_KEY`)

---

## Method A: Full Project Files (Local Server)

Use this if you have the complete repository and want to run the MCP tools on your own machine.

### 1. Clone the repository

```bash
git clone https://github.com/MuhammadHuzaifaFarrukh/PUCIT_CGPA_Calculator_MCP_Server.git
cd PUCIT_CGPA_Calculator_MCP_Server
```

### 2. Install server dependencies

From the repository root:

```bash
pip install -r requirements.txt
```

### 3. Install agent dependencies

```bash
cd agent
pip install -r requirements.txt
```

or install the packages directly:

```bash
pip install python-dotenv fastmcp langchain langchain-core langchain-groq langgraph-checkpoint-sqlite
```

### 4. Configure environment variables

Copy `.env.example` to `.env` inside the `agent/` directory and fill in your values:

```env
GROQ_API_KEY="YOUR_KEY"
MCP_URL=http://127.0.0.1:8000/mcp
FASTMCP_KEY=
```

### 5. Start the MCP server

Open a terminal in the repository root (where `server.py` is) and run:

```bash
python server.py   # or: py server.py
```

Keep it running so it listens on `http://127.0.0.1:8000/mcp`.

### 6. Start the agent

Open a **second** terminal in the `agent/` folder and run:

```bash
python main.py   # or: py main.py
```

---

## Method B: Agent Files Only (Hosted Server)

Use this if you do **not** have the server files and do not want to run the server yourself. You only need the `agent/` folder. The tools run on the hosted server.

### 1. Get the agent files

Clone the repository and use only the `agent/` folder:

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>/agent
```

Or download just the `agent/` folder and open a terminal inside it.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

or install the packages directly:

```bash
pip install python-dotenv fastmcp langchain langchain-core langchain-groq langgraph-checkpoint-sqlite
```

### 3. Configure environment variables

Copy `.env.example` to `.env` inside the `agent/` directory and fill in your own keys:

```env
GROQ_API_KEY="YOUR_GROQ_API_KEY"
MCP_URL=https://pucit-cgpa-advisor.fastmcp.app/mcp
FASTMCP_KEY="YOUR_FASTMCP_BEARER_TOKEN"
```

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Your own Groq API key for the LLM |
| `MCP_URL` | The hosted MCP endpoint shown above |
| `FASTMCP_KEY` | A valid bearer token that authorizes access to the hosted server |

### 4. Run the agent

```bash
python main.py   # or: py main.py
```

No local `server.py` is needed. Your CLI and `cgpa_memory.db` run on your computer, and tool calls are sent to the hosted server.

---

## Chatting with the Advisor

Once `main.py` is running (with either method):

1. When prompted, enter a student name or `thread_id`. Existing saved threads are shown on startup.
2. Ask an advising, course, or GPA planning question and watch the streamed tool and advisor output.
3. Use `/history`, `/switch`, or `/forget` at any time, or type `exit` to quit.

---

## Error Handling & Recovery

- **Before each turn and on any exception**, `repair_dangling_tool_calls` inspects the active thread's state for `AIMessage` tool calls that never received a matching `ToolMessage`. It patches them with a recovery `ToolMessage` so later turns stay intact.
- **Connection drops and streaming errors** during a turn or MCP session are caught and surfaced cleanly in the CLI. You can retry, switch threads, or check the server without the program crashing.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Connection refused / timeout | Check that `MCP_URL` is correct and ends in `/mcp`. For Method A, make sure `server.py` is still running |
| `401` / unauthorized | Check that `FASTMCP_KEY` is a valid bearer token and is set in `agent/.env` (Method B) |
| Tools not found | Make sure `MCP_URL` points to the right server and that it is running the latest `server.py` and `tools.py` |
| Groq errors | Verify `GROQ_API_KEY` is valid and has not hit its rate limit |
