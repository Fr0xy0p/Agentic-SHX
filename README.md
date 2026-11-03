# ⚡ Agentic-SHX

**Agentic-SHX** is an autonomous terminal coding agent and CLI tool inspired by Antigravity CLI and Claude Code. It empowers developers to plan, write, refactor, debug, test, and commit code entirely from the terminal using state-of-the-art LLMs (Gemini 2.5/3, Claude 3.7 Sonnet, OpenAI, and local Ollama models).

---

## 🌟 Key Features

- **Autonomous ReAct Engine**: Iterative planning, execution, and observation loop that investigates context, performs surgical edits, and runs tests to verify its work.
- **Multi-Provider LLM Abstraction**:
  - **Google Gemini**: Native streaming and tool-calling for `gemini-2.5-flash`, `gemini-2.5-pro`, and `gemini-2.0-flash`.
  - **Anthropic Claude**: Full support for `claude-3-7-sonnet`, `claude-3-5-sonnet`, and `haiku`.
  - **OpenAI & Compatible**: Supports `gpt-4o`, `o3-mini`, `openrouter/*`, and local models via `ollama/*` (`ollama/qwen2.5-coder:7b`).
- **Interactive Terminal UI (TUI)**:
  - Rich streaming Markdown and thought/reasoning token display.
  - Colorized code diff viewer and execution status cards.
  - Multi-line command prompt with auto-completion and history.
  - Slash command shortcuts: `/diff`, `/model`, `/compact`, `/status`, `/tools`, `/clear`.
- **Intelligent Safety & Permissions**:
  - Automatically identifies read-only inspection commands (`ls`, `cat`, `git status`, `grep`) to minimize user interruption.
  - Blocks catastrophic commands (`rm -rf /`, `mkfs`, fork bombs).
  - Prompts for confirmation on moderate/high-risk operations with session allow-listing (`always allow for this session`).
- **Surgical File & Git Tools**:
  - Exact target-replacement editing (`edit_file`) that maintains formatting.
  - Sliced reading with line numbers (`read_file`).
  - Regex search (`search_files`) and globbing (`list_files`).
  - Subprocess shell execution (`bash`) with timeout protection and output truncation.
- **Custom Project Rules**: Automatically ingests `.shxrules` or `AGENTIC.md` from the repository root to adapt to your project's coding standards.

---

## 🏗️ Architecture

```
Agentic-SHX/
├── agentic_shx/
│   ├── cli.py                  # CLI argument parsing and session kickoff
│   ├── config.py               # User settings and ~/.agentic_shx persistence
│   ├── agent/
│   │   ├── loop.py             # Autonomous ReAct execution loop
│   │   ├── context.py          # Message history, compaction, token tracking
│   │   └── prompts.py          # Dynamic system prompt & repo environment discovery
│   ├── providers/
│   │   ├── base.py             # Abstract provider & ToolCall schemas
│   │   ├── factory.py          # Model resolution & provider instantiator
│   │   ├── gemini_provider.py  # Google Gemini streaming tool-calling API
│   │   ├── claude_provider.py  # Anthropic Claude streaming messages API
│   │   └── openai_provider.py  # OpenAI, OpenRouter, and Ollama API
│   ├── tools/
│   │   ├── base.py             # ToolResult & BaseTool interfaces
│   │   ├── registry.py         # Discoverable tool registry
│   │   ├── bash.py             # Shell execution with timeout & output limits
│   │   ├── file_ops.py         # Surgical read, write, and replace tools
│   │   ├── search.py           # Regex grep & glob list tools
│   │   └── git_ops.py          # Git diff & status inspection tools
│   ├── safety/
│   │   ├── analyzer.py         # Shell command risk heuristics (SAFE/MODERATE/DANGEROUS/BLOCKED)
│   │   └── permissions.py      # Session permission manager & allow-listing
│   └── ui/
│       ├── console.py          # Rich console theme & startup banner
│       ├── renderers.py        # Syntax-highlighted diffs, tool cards, and markdown
│       ├── approval.py         # Interactive prompt for tool execution approval
│       └── repl.py             # prompt_toolkit REPL loop with slash commands
└── tests/                      # Full pytest suite
```

---

## 🚀 Quickstart

### 1. Installation

Clone and install in editable mode:

```bash
git clone https://github.com/your-username/Agentic-SHX.git
cd Agentic-SHX

python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Configure API Keys

Set your preferred provider key in your environment or in a local `.env` file:

```bash
# Google Gemini (Default)
export GEMINI_API_KEY="your-gemini-api-key"

# Anthropic Claude
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# OpenAI / OpenRouter
export OPENAI_API_KEY="your-openai-api-key"
```

---

## 💻 Usage

### Interactive REPL Mode

Launch the interactive assistant in your current workspace:

```bash
shx
```

Or specify a model directly:

```bash
# Use Claude 3.7 Sonnet
shx -m claude-3-7-sonnet

# Use Google Gemini 2.5 Pro
shx -m gemini/gemini-2.5-pro

# Use local Ollama model
shx -m ollama/qwen2.5-coder:7b
```

### Headless / One-Shot Mode (`-p`)

Run a single prompt and exit, perfect for CI/CD or fast shell scripts:

```bash
shx -p "Find all failing tests, fix the assertions, and verify with pytest"
```

### Slash Commands in REPL

| Command | Description |
|---|---|
| `/help` | Display command guide and tips |
| `/diff` | View active git diff with syntax highlighting |
| `/status` | View repository branch, dirty files, and token count |
| `/model <name>` | Switch the active LLM dynamically during a session |
| `/compact` | Prune old tool outputs from context to save tokens |
| `/tools` | List all registered tools and parameter specifications |
| `/clear` | Clear conversation history and reset memory |
| `/exit` | Exit the application |

---

## 🛡️ Safety & Permission Levels

Agentic-SHX categorizes every action into 4 security tiers:

1. **SAFE (Auto-Approved)**: Read-only inspection commands (`ls`, `cat`, `git status`, `git log`, `grep`, `pwd`) execute instantly without prompting.
2. **MODERATE**: Normal build commands, dependency installation, and file modifications prompt for confirmation:
   - `[y]es`: Allow once
   - `[a]lways`: Allow all matching commands for this session
   - `[n]o`: Reject tool call and feed refusal back to the model
   - `a[b]ort`: Cancel the agent task entirely
3. **DANGEROUS**: High-risk actions (`sudo`, `git reset --hard`, `git push --force`, piping web scripts to shell) display highlighted warnings and require explicit confirmation.
4. **BLOCKED**: Catastrophic actions (`rm -rf /`, formatting disks, fork bombs) are halted immediately by safety rules.

---

## 🧪 Testing

Run the test suite:

```bash
pytest -v
```

---

## 📄 License

MIT License.
