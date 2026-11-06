# ⚡ Agentic-SHX (`agn` / `shx`)

**Agentic-SHX** is a production-grade autonomous terminal coding agent and shell assistant matching the architecture and capabilities of Google's **Antigravity CLI** (`agy`) and Claude Code. 

It combines hierarchical subagent delegation, background task supervision, structured artifact generation, specialized skills, and session transcript persistence—with multi-provider LLM support (**Gemini 3.8 Flash**, Claude 3.7 Sonnet, Groq, OpenAI, and local Ollama models) and seamless parent shell navigation.

---

## 🌟 Key Capabilities (Antigravity Parity)

- **Hierarchical Subagent Delegation**:
  - `invoke_subagent`: Spawns autonomous subagents with isolated context and specialized roles:
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
- **Specialized Skills System**:
  - Discovers specialized skill packages in `.shx/skills/<skill-name>/SKILL.md` or `~/.agentic_shx/skills/`.
  - Injects available skills into the system prompt; reads full instructions via `read_skill`.
- **Session Trajectory & Resumption**:
  - Records every turn, thought token, tool invocation, and observation into append-only `transcript.jsonl`.
  - Resume any past conversation seamlessly: `agn -r` or `agn -r <session_id>`.
- **Multi-Provider LLM Engine**:
  - **Google Gemini**: Native streaming and tool-calling for `gemini-3.8-flash` (default), `gemini-2.5-flash`, and `gemini-2.5-pro`.
  - **Anthropic Claude**: Full streaming tool use for `claude-3-7-sonnet`, `claude-3-5-sonnet`, and `haiku`.
  - **Groq**: Ultra-fast inference with `groq/llama-3.3-70b-versatile`, `groq/llama-3.1-8b-instant`, and `groq/deepseek-r1-distill-llama-70b`.
  - **OpenAI & Compatible**: Supports `gpt-4o`, `o3-mini`, `openrouter/*`, and local models via `ollama/*`.
- **Shell Integration & Directory Navigation**:
  - Automatically navigates the parent terminal's working directory (`cd`) and environment (`export`) via `SHX_CMD_FILE` handoff.
  - Automatic fallback to system clipboard (`pbcopy`, `wl-copy`, `clip`).
  - Offline cryptic flags database and command explainer (`agn explain "<cmd>"` and `/explain`).
- **Terminal UI (TUI)**:
  - Antigravity visual banners, step counters (`[Step 1/30]`), live thought streams, syntax-highlighted diffs, and execution status cards.
  - Slash commands: `/goal`, `/plan`, `/explain`, `/tasks`, `/artifacts`, `/skills`, `/diff`, `/compact`, `/resume`, `/model`, `/clear`.

---

## 🏗️ Architecture

```
Agentic-SHX/
├── agentic_shx/
│   ├── cli.py                  # CLI entrypoint, argument parsing, subcommands (info, explain, setup, init)
│   ├── config.py               # User settings and ~/.agentic_shx persistence
│   ├── shell_integration.py    # Shell state detection, parent handoff (SHX_CMD_FILE), and clipboard
│   ├── explainer.py            # Offline database of cryptic Unix flags and command explanation
│   ├── agent/
│   │   ├── loop.py             # ReAct loop with step indicators, artifact & task hooks
│   │   ├── context.py          # Message trajectory, compaction, token tracking
│   │   └── prompts.py          # Dynamic system prompt, skills context, repo environment & directory sample
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
│   │   ├── bash.py             # Shell execution with timeout, background tasks & cd directory tracking
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
└── tests/                      # Full pytest suite (31 unit & integration tests)
```

---

## 🚀 Quickstart

### 1. Installation

```bash
cd Agentic-SHX
source .venv/bin/activate
pip install -e .
```

This creates the commands `agn`, `shx`, and `agentic-shx` globally in your environment.

### 2. Configure API Keys

Set your preferred provider key in your environment or in a local `.env` file:

```bash
# Google Gemini (Default - gemini-3.8-flash)
export GEMINI_API_KEY="your-gemini-key"

# Anthropic Claude
export ANTHROPIC_API_KEY="your-claude-key"

# Groq (Llama 3.3, DeepSeek R1)
export GROQ_API_KEY="your-groq-key"

# OpenAI / OpenRouter
export OPENAI_API_KEY="your-openai-key"
```

### 3. Shell Integration (Directory Navigation)

To enable automatic terminal navigation (`cd`) directly in your parent shell:

```bash
# One-click automatic setup (configures ~/.zshrc or ~/.bashrc)
agn setup

# Or manually add to ~/.zshrc:
eval "$(agn init zsh)"
```

Then reload your terminal (`source ~/.zshrc`). Now executing `cd` commands inside the agent navigates your active terminal window!

---

## 💻 Commands & Usage

### Interactive Mode

Launch the Antigravity-style interactive coding agent:

```bash
agn
# or
shx
```

### Natural Language Execution

Execute a single prompt directly from the shell:

```bash
agn "navigate into my project and run the tests"
# or
agn -p "Check git status, find all TODOs, and summarize them"
```

### Inspect Environment & Health

Audit your system context, active model, and API keys:

```bash
agn info
```

### Explain Shell Commands & Cryptic Flags

Break down any cryptic shell command with local flag lookup and AI analysis:

```bash
agn explain "tar -xzvf archive.tar.gz"
agn explain "find . -type f -name '*.py' -mtime -7"
```

### Resume Previous Sessions

```bash
# Resume your latest conversation
agn -r

# Or resume a specific session by ID
agn -r c7f91a2b
```

---

## ⌨️ Antigravity Slash Commands

Inside the interactive REPL (`agn ❯ `):

| Command | Action |
|---|---|
| `/goal <task>` | Run a long-running, thorough autonomous goal without stopping |
| `/plan` | Request agent to draft an implementation plan artifact |
| `/explain <cmd>` | Break down cryptic flags and explain a shell command |
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
| `/help` | Detailed command manual and shortcuts |
| `/exit` | Exit the application |

---

## 🛡️ Safety & Permission Guardrails

Agentic-SHX analyzes every action before execution:

1. **SAFE (Auto-Approved)**: Read-only inspection commands (`ls`, `pwd`, `cat`, `git status`, `git log`, `grep`) execute instantly without prompting.
2. **MODERATE**: File modifications, package installs, and builds prompt for confirmation (`[y]es`, `[a]lways for session`, `[n]o`, `a[b]ort`).
3. **DANGEROUS**: High-risk actions (`sudo`, `git reset --hard`, `git push --force`) display prominent warnings.
4. **BLOCKED**: Catastrophic commands (`rm -rf /`, `mkfs`, fork bombs) are halted immediately by safety rules.

---

## 🧪 Testing

Run the full test suite covering all tools, safety guardrails, background tasks, subagents, shell integration, and ReAct loop:

```bash
pytest -v
```

```text
tests/test_agent_loop.py .                                               [  3%]
tests/test_artifacts.py .                                                [  6%]
tests/test_cli.py ......                                                 [ 25%]
tests/test_providers.py .....                                            [ 41%]
tests/test_safety.py ....                                                [ 54%]
tests/test_sessions.py .                                                 [ 58%]
tests/test_shell_integration.py .....                                    [ 74%]
tests/test_skills.py .                                                   [ 77%]
tests/test_subagents.py .                                                [ 80%]
tests/test_tasks.py .                                                    [ 83%]
tests/test_tools.py .....                                                [100%]
============================== 31 passed in 2.24s ==============================
```

---

## 📄 License

MIT License.
