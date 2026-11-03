# ⚡ Agentic-SHX

**Agentic-SHX** is a production-grade autonomous terminal coding agent matching the architecture and capabilities of Google's **Antigravity CLI** (`agy`) and Claude Code. It provides hierarchical subagent delegation, background task supervision, structured artifact generation, specialized skills, and full session transcript persistence—with multi-provider LLM support (Gemini, Claude 3.7 Sonnet, Groq, OpenAI, and local Ollama models).

---

## 🌟 Key Capabilities (Antigravity Parity)

- **Hierarchical Subagent Delegation**:
  - `invoke_subagent`: Spawns autonomous subagents with isolated context and roles:
    - `research`: Read-only explorer that inspects code and symbols without cluttering the main context.
    - `planner`: Architectural decomposition and milestone planner.
    - `self`: Full-capability child coder.
  - `define_subagent`: Dynamically define specialized subagents with custom system prompts and tool access.
- **Background Task & Daemon Management**:
  - `manage_task`: Non-blocking process execution for dev servers, file watchers, test suites, and builds.
  - Supports `wait_ms` (wait briefly, then background if still running) and `is_daemon=true`.
  - Actions: `list`, `status` (tail recent output logs), `send_input`, `kill`.
- **Structured Artifacts System**:
  - `create_artifact`: Generates structured markdown documents (implementation plans, design specs, experiment logs, architecture reports) saved under `~/.agentic_shx/artifacts/<session_id>/`.
  - Interactive approval loops: When `request_feedback=True` is specified, the CLI prompts the user to review and approve the plan before execution.
- **Skills System**:
  - Discovers specialized skill packages in `.shx/skills/<skill-name>/SKILL.md` or `~/.agentic_shx/skills/`.
  - Injects available skills into the system prompt; reads full instructions via `read_skill`.
- **Session Trajectory & Resumption**:
  - Records every turn, thought token, tool invocation, and observation into `transcript.jsonl`.
  - Resume any past conversation seamlessly: `shx -r` or `shx -r <session_id>`.
- **Multi-Provider LLM Engine**:
  - **Google Gemini**: Native streaming and tool-calling for `gemini-2.5-flash`, `gemini-2.5-pro`, and `gemini-2.0-flash`.
  - **Anthropic Claude**: Full streaming tool use for `claude-3-7-sonnet`, `claude-3-5-sonnet`, and `haiku`.
  - **Groq**: Ultra-fast inference with `groq/llama-3.3-70b-versatile`, `groq/llama-3.1-8b-instant`, and `groq/deepseek-r1-distill-llama-70b`.
  - **OpenAI & Compatible**: Supports `gpt-4o`, `o3-mini`, `openrouter/*`, and local models via `ollama/*`.
- **Terminal UI (TUI)**:
  - Antigravity visual banners, step counters (`[Step 1/30]`), live thought streams, syntax-highlighted diffs, and execution status cards.
  - Slash commands: `/goal`, `/plan`, `/tasks`, `/artifacts`, `/skills`, `/diff`, `/compact`, `/resume`, `/model`, `/clear`.

---

## 🏗️ Architecture

```
Agentic-SHX/
├── agentic_shx/
│   ├── cli.py                  # Entrypoint, argument parsing, banner, session kickoff
│   ├── config.py               # User settings and ~/.agentic_shx persistence
│   ├── agent/
│   │   ├── loop.py             # ReAct loop with step indicators, artifact & task hooks
│   │   ├── context.py          # Message trajectory, compaction, token tracking
│   │   └── prompts.py          # Dynamic system prompt, skills context, repo environment
│   ├── session/
│   │   └── manager.py          # Session transcript logging (transcript.jsonl) & resumption
│   ├── tasks/
│   │   ├── manager.py          # Background subprocess supervisor, logs, status
│   │   └── tool.py             # manage_task tool (list, status, send_input, kill)
│   ├── subagents/
│   │   ├── manager.py          # Subagent hierarchy (research, planner, self)
│   │   └── tools.py            # invoke_subagent and define_subagent tools
│   ├── artifacts/
│   │   ├── manager.py          # Markdown artifact storage and metadata
│   │   └── tool.py             # create_artifact tool
│   ├── skills/
│   │   ├── manager.py          # Skill discovery (.shx/skills/ and ~/.agentic_shx/skills/)
│   │   └── tool.py             # read_skill tool
│   ├── providers/
│   │   ├── base.py             # Abstract provider & ToolCall schemas
│   │   ├── factory.py          # Model resolution & provider instantiator
│   │   ├── gemini_provider.py  # Google Gemini streaming tool-calling API
│   │   ├── claude_provider.py  # Anthropic Claude streaming messages API
│   │   ├── groq_provider.py    # Groq ultra-fast Llama & DeepSeek inference
│   │   └── openai_provider.py  # OpenAI, OpenRouter, and Ollama API
│   ├── tools/
│   │   ├── base.py             # ToolResult & BaseTool interfaces
│   │   ├── registry.py         # Discoverable tool registry
│   │   ├── bash.py             # Shell execution with timeout & background task support
│   │   ├── file_ops.py         # Surgical read, write, and replace tools
│   │   ├── search.py           # Regex grep & glob list tools
│   │   └── git_ops.py          # Git diff & status inspection tools
│   ├── safety/
│   │   ├── analyzer.py         # Shell command risk heuristics (SAFE/MODERATE/DANGEROUS/BLOCKED)
│   │   └── permissions.py      # Session permission manager & allow-listing
│   └── ui/
│       ├── console.py          # Rich console theme & startup banner
│       ├── renderers.py        # Diffs, tool cards, artifact cards, and markdown
│       ├── approval.py         # Interactive prompt for tool execution approval
│       └── repl.py             # Antigravity REPL loop with slash commands
└── tests/                      # Full pytest suite (20 unit & integration tests)
```

---

## 🚀 Quickstart

### 1. Installation

```bash
cd Agentic-SHX
source .venv/bin/activate
pip install -e .
```

### 2. Configure API Keys

Add keys to your shell or local `.env`:

```bash
# Google Gemini (Default)
export GEMINI_API_KEY="your-gemini-key"

# Anthropic Claude
export ANTHROPIC_API_KEY="your-claude-key"

# Groq (Llama 3.3, DeepSeek R1)
export GROQ_API_KEY="your-groq-key"

# OpenAI / OpenRouter
export OPENAI_API_KEY="your-openai-key"
```

---

## 💻 Usage & Commands

### Interactive Mode

```bash
shx
```

### Resume Previous Sessions

```bash
# Resume latest session
shx -r

# Or resume a specific session ID
shx -r c7f91a2b
```

### Antigravity Slash Commands

| Command | Action |
|---|---|
| `/goal <task>` | Run a long-running, thorough autonomous goal without stopping |
| `/plan` | Request agent to draft an implementation plan artifact |
| `/tasks` | List running background processes, watchers, and servers |
| `/artifacts` | List and review created markdown documents |
| `/skills` | Browse specialized skills loaded from `.shx/skills/` |
| `/diff` | View active git diff with syntax highlighting |
| `/model <name>` | Switch active LLM dynamically during a session |
| `/compact` | Prune older tool observations to conserve token context |
| `/resume` | List recent conversation sessions |
| `/status` | View repository branch, dirty files, and token count |
| `/tools` | List all registered tools and parameter specifications |
| `/clear` | Clear conversation history and reset memory |
| `/exit` | Exit the application |

---

## 🧪 Testing

Run all 20 unit and integration tests:

```bash
pytest -v
```

---

## 📄 License

MIT License.
