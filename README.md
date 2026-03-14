# 🐦 Murmur

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI](https://img.shields.io/pypi/v/murmur-agent)](https://pypi.org/project/murmur-agent/)

```text
      ..---..
    .'  _    `.
    |  (o)    |   "A coordinated swarm of AI agents
     \   _   /     for your codebase."
      `-----'
```

Murmur is a hierarchical multi-agent AI coding CLI. By executing `murmur <command> "<task>"` inside any codebase, Murmur autonomously decomposes your task into a tree of sub-tasks. It spawns a specialized autonomous agent for each sub-task, routing execution via LangGraph, and orchestrates them using an `OverallState` whiteboard memory layer to avoid context contamination or merge conflicts.

## 🏗 Architecture

```mermaid
flowchart TD
    User([User CLI]) --> Supervisor[Top-Level Supervisor]
    Supervisor --> Router[Task Router]
    Router --> Refactor[Refactor Team Subgraph]
    Router --> Test[Test Team Subgraph]
    Router --> Doc[Doc Team Subgraph]
    Router --> Review[Review Agent Node]
    
    Refactor --> Integrator[Integrator Node]
    Test --> Integrator
    Doc --> Integrator
    Review --> Integrator
    
    Integrator --> Git([Final Commit / Merge])
    
    subgraph MCP Layer [Model Context Protocol (MCP) Servers]
        Workspace[Built-In: File/Git/Test]
        SeqThinking[sequential-thinking]
        Docfork[docfork]
        Context7[context7]
        Ref[ref]
        Kindly[kindly-web-search]
        Tavily[tavily]
        Exa[exa]
        Linkup[linkup]
    end
    
    Supervisor -.-> MCP Layer
    Refactor -.-> MCP Layer
    Test -.-> MCP Layer
    Doc -.-> MCP Layer
    Review -.-> MCP Layer
```

## 📝 Prerequisites

- Python 3.11+
- Node.js 18+ and `npx` (for sequential-thinking and docfork)
- `uvx` (for kindly-web-search)
- `git`
- At least one supported LLM API Key (OpenAI, Anthropic, Google Gemini, Ollama, Groq, or NVIDIA)

## 📦 Installation

```bash
pip install murmur-agent
# OR using uv:
uv tool install murmur-agent
```

## 🚀 Quick Start

1. Initialize and configure your LLM:
   ```bash
   murmur config --llm openai:gpt-4o
   ```
2. Navigate to your codebase:
   ```bash
   cd /path/to/repo
   ```
3. Run Murmur:
   ```bash
   murmur run "Refactor the authentication module to be asynchronous and update the tests."
   ```

## 💻 CLI Commands

- `murmur run "<task>"`: Full pipeline execution (plan + apply). Initialises graph, spins up MCP clients, runs supervisor graph.
  *Example:* `murmur run "Add a Redis caching layer to the database module"`
- `murmur plan "<task>"`: Planning only. Analyses the repo and prints a structured task plan. Writes nothing.
  *Example:* `murmur plan "Upgrade React to v18"`
- `murmur apply [--plan-id ID]`: Execute a previously generated plan.
  *Example:* `murmur apply --plan-id abc12345`
- `murmur refactor "<description>"`: Alias for `plan` + `apply`.
- `murmur add-tests [--module PATH]`: Generate tests for a specific module or the entire codebase.
  *Example:* `murmur add-tests --module src/utils`
- `murmur review`: Code review of recent Git changes. Prints structured findings.
- `murmur doc [--module PATH]`: Generate docstrings and README sections. 
- `murmur status`: View live progress of running runs, streamed via Rich.
- `murmur config --llm <provider/model>`: Set default LLM (e.g., `openai:gpt-4o`, `anthropic:claude-3-5-sonnet-20240620`).
- `murmur memory list`: View all stored task runs.
- `murmur memory clear`: Clear all persistent states and the RAG index.

### Global Options

- `--repo-path PATH`: Target directory (default: current directory).
- `--model STR`: Override the default model configured in `.murmur/config.yaml`.
- `--dry-run`: Evaluate diffs without writing them nor branching.
- `--max-workers INT`: Limit the top-level simultaneous sub-agents.
- `--max-depth INT`: Allow agents to recursively split into sub-agents up to a certain depth.
- `--no-commit`: Agents will merge, but will drop the final commit action.
- `--review`: The Integration agent pauses. Allows for human inspection.
- `--interactive`: Interactive mode requires 'Y' for every task.
- `--plan-id STR`: Force apply to a specific snapshot ID.
- `--verbose / -v`: Emits DEBUG logs and traces all MCP tools.

## 🔐 Environment Variables

| Variable | Description |
|---|---|
| `MURMUR_MODEL` | Default LLM model string (e.g., `openai:gpt-4o`) |
| `OPENAI_API_KEY` | OpenAI API Auth |
| `ANTHROPIC_API_KEY` | Anthropic API Auth |
| `GOOGLE_API_KEY` | Google API Auth |
| `NVIDIA_API_KEY` | NVIDIA AI Endpoints API |
| `GROQ_API_KEY` | Groq API Key |
| `LINKUP_API_KEY` | Optional: Linkup Web Search |
| `EXA_API_KEY` | Optional: Exa Neural Web Search |
| `TAVILY_API_KEY` | Optional: Tavily AI Search |
| `REF_API_KEY` | Optional: ref.tools API Key |
| `CONTEXT7_API_KEY` | Optional: Context7 API Key |
| `SERPER_API_KEY` | Optional: Serper API for `kindly-web-search` |
| `DOCFORK_API_KEY` | Optional: Docfork API Key |
| `LANGCHAIN_API_KEY` | Optional: LangSmith API Tracing |
| `LANGCHAIN_TRACING_V2` | Set to `true` to enable tracing |

## ⚙️ Configuration File (`.murmur/config.yaml`)

You can set global defaults in the `.murmur/config.yaml` or `~/.config/murmur/config.yaml`. Example:

```yaml
model: openai:gpt-4o
temperature: 0.2
max_tokens: 4096
max_workers: 4
max_depth: 3
rag_enabled: true
rag_backend: chroma
auto_branch: true
auto_commit: true
snapshot_interval: 30
```

## 🔌 Supported MCP Servers

| Server Name | Transport | Purpose | Requirement | Key Env Var |
|---|---|---|---|---|
| `workspace` | stdio | File system, git diffs, testing via FastMCP | Required | N/A |
| `sequential-thinking` | stdio | Structured reasoning loops | Required | N/A |
| `docfork` | stdio | Library and Framework documentation lookup | Optional | `DOCFORK_API_KEY` |
| `kindly-web-search` | stdio | Aggregated SERP functionality | Optional | `SERPER_API_KEY` |
| `linkup` | streamable_http | Deep Web Search | Optional | `LINKUP_API_KEY` |
| `exa` | streamable_http | GitHub / Docs Search | Optional | `EXA_API_KEY` |
| `tavily` | streamable_http | LLM Optimized search | Optional | `TAVILY_API_KEY` |
| `ref` | streamable_http | API/Documentation Token-efficient Search | Optional | `REF_API_KEY` |
| `context7` | streamable_http | Versioned specific API docs | Optional | `CONTEXT7_API_KEY` |

## 💾 The OverallState Whiteboard

Instead of typical multi-agent systems where context rapidly dilutes, Murmur relies on a shared `OverallState` TypedDict. The Supervisor assigns isolated data subsets into task definitions (using LangGraph Memory Storage), ensuring that the `doc_writer` doesn't cross threads with the `test_writer`. File locking is observed tightly at the state level to ensure merge conflict prevention. Branches are isolated initially.

## 🌿 Git Strategy

During execution, `murmur` will generate feature branches using `murmur/<session_id[:8]>/<task_id>`. As each worker team wraps up execution, branches are merged into `murmur/<session>`. Once all workers flag `DONE`, the Integrator node performs a `git merge`. If conflicts arise, it utilizes an AI Diff Resolver. Finally, an automated `chore(murmur)` commit concludes the workflow (unless `--no-commit` is specified).

## 🧠 Memory and RAG

LangGraph `SqliteSaver` checkpointer ensures all sessions persist locally over `murmur.db`, allowing commands like `murmur apply` to resume seamlessly.
To accommodate enormous repositories, Murmur generates a local ChromaDB or FAISS index mapped across ast-parsed functions. Workers request snippets through `RAGIndex.get_context_for_task()`.

## 🔄 Infinite Recursion via Depth Limits

Sub-agents can dynamically spin off children via the `spawn_sub_agent` tool. This enables Murmur to scale massively, limited only by `max_depth` (default 3) stored inside `OverallState["current_depth"]`.

## 🔭 Observing Execution with LangSmith

Set `LANGCHAIN_API_KEY` and `LANGCHAIN_TRACING_V2=true` in your environment. Since Murmur leverages LangGraph heavily, all state transitions map instantly into LangSmith's trace UI.

## 🛠 Adding a Custom MCP Server

Inject new external tools globally by patching `mcp_servers` configuration in `.murmur/config.yaml`:
```yaml
mcp_servers:
  "custom-db":
    transport: stdio
    command: npx
    args: ["-y", "@server/my-db-mcp"]
```
It immediately loads the capabilities onto the client via `MultiServerMCPClient`.

## 👥 Adding Agent Teams

Creating a new team entails editing `src/murmur/agents/`:
1. Use `create_react_agent` linked heavily with specific assigned tools (`mcp_client.get_tools_for_role(...)`).
2. Attach it into a team supervisor utilizing `create_supervisor(agents=[worker])`.
3. Dispatch it directly inside `router.py`.

## ✅ Running Tests

To develop or test locally:
```bash
make install
make test
```

## ⚖️ License and Contributing

Murmur is distributed under the MIT license. See `CONTRIBUTING.md` for our standardized procedures on pull requests.
