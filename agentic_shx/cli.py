"""CLI Entrypoint for Agentic-SHX."""

import sys
import argparse
from pathlib import Path
from typing import Optional

from agentic_shx import __version__
from agentic_shx.config import Settings
from agentic_shx.providers.factory import get_provider
from agentic_shx.tools.registry import ToolRegistry
from agentic_shx.safety.permissions import PermissionManager
from agentic_shx.agent.prompts import build_system_prompt, get_git_summary
from agentic_shx.agent.context import ConversationContext
from agentic_shx.agent.loop import AgentLoop
from agentic_shx.session.manager import SessionManager
from agentic_shx.tasks.manager import TaskManager
from agentic_shx.artifacts.manager import ArtifactManager
from agentic_shx.skills.manager import SkillManager
from agentic_shx.subagents.manager import SubagentManager
from agentic_shx.ui.console import console, print_welcome_banner
from agentic_shx.ui.renderers import (
    render_markdown,
    render_thought,
    render_step_header,
    render_tool_start,
    render_tool_result,
    render_artifact_card,
    render_subagent_event
)
from agentic_shx.ui.approval import request_tool_approval
from agentic_shx.ui.repl import start_repl

def main() -> None:
    # Handle 'shx init <shell>' for shell integration (e.g. in ~/.zshrc or ~/.bashrc)
    if len(sys.argv) >= 2 and sys.argv[1] == "init":
        shell = sys.argv[2] if len(sys.argv) > 2 else "zsh"
        local_bin = Path.home() / ".local" / "bin"
        if shell in ("zsh", "bash"):
            print(f"""# Agentic-SHX Shell Integration for {shell}
export PATH="{local_bin}:$PATH"
alias shx="command shx"
""")
        sys.exit(0)

    parser = argparse.ArgumentParser(
        prog="shx",
        description="Agentic-SHX: Autonomous Terminal Coding Agent"
    )
    parser.add_argument(
        "-p", "--prompt",
        type=str,
        help="Non-interactive mode: run a single prompt and exit."
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        help="Override active LLM model (e.g. gemini/gemini-2.5-flash, claude-3-7-sonnet, groq/llama-3.3-70b-versatile, gpt-4o, ollama/qwen2.5-coder)."
    )
    parser.add_argument(
        "-r", "--resume",
        type=str,
        nargs="?",
        const="latest",
        help="Resume previous session by ID, or resume latest."
    )
    parser.add_argument(
        "-C", "--cwd",
        type=str,
        default=".",
        help="Target working directory for the agent session."
    )
    parser.add_argument(
        "--temperature", "-t",
        type=float,
        default=None,
        help="Sampling temperature (0.0 to 1.0)."
    )
    parser.add_argument(
        "--ask-all",
        action="store_true",
        help="Prompt for confirmation before every tool execution, including read-only commands."
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"Agentic-SHX v{__version__}"
    )

    args = parser.parse_args()

    # Load configuration
    settings = Settings.load()
    if args.model:
        settings.model = args.model
    if args.temperature is not None:
        settings.temperature = args.temperature
    if args.ask_all:
        settings.auto_approve_safe_commands = False

    target_cwd = Path(args.cwd).resolve()

    # Initialize Provider
    try:
        provider = get_provider(
            model=settings.model,
            api_keys=settings.api_keys,
            api_bases=settings.api_bases
        )
    except Exception as e:
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        console.print("[dim]Set your API key via environment variable (e.g. GEMINI_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY, GROQ_API_KEY).[/dim]")
        sys.exit(1)

    # Initialize Session Manager & Resumption
    session_id = None
    if args.resume:
        if args.resume == "latest":
            past = SessionManager.list_all_sessions()
            if past:
                session_id = past[0]["id"]
                console.print(f"[dim]Resuming latest session: {session_id}[/dim]")
        else:
            session_id = args.resume

    session_mgr = SessionManager(session_id=session_id)

    # Subsystems Initialization
    task_mgr = TaskManager()
    artifact_mgr = ArtifactManager(session_id=session_mgr.session_id)
    skill_mgr = SkillManager(workspace_cwd=target_cwd)

    # Base registry for subagents
    base_registry = ToolRegistry.create_default(cwd=str(target_cwd))
    subagent_mgr = SubagentManager(
        provider=provider,
        base_registry=base_registry,
        cwd=str(target_cwd)
    )

    # Main Tool Registry with all subsystems
    tool_registry = ToolRegistry.create_default(
        cwd=str(target_cwd),
        task_manager=task_mgr,
        artifact_manager=artifact_mgr,
        subagent_manager=subagent_mgr,
        skill_manager=skill_mgr
    )

    permission_manager = PermissionManager(
        auto_approve_safe=settings.auto_approve_safe_commands
    )

    # System Prompt with Skills context
    skills_prompt = skill_mgr.get_skills_prompt()
    system_prompt = build_system_prompt(cwd=target_cwd, skills_prompt=skills_prompt)
    context = ConversationContext(system_prompt=system_prompt)

    # Replay past messages if resuming
    if args.resume:
        events = session_mgr.load_events()
        for ev in events:
            if ev.type == "USER_INPUT":
                context.add_user_message(str(ev.content))
            elif ev.type == "MODEL_OUTPUT":
                context.add_assistant_message(str(ev.content))

    # Streaming token handler
    def handle_content_chunk(chunk: str):
        console.print(chunk, end="", highlight=False)

    # Build the Agent Loop
    loop = AgentLoop(
        provider=provider,
        tool_registry=tool_registry,
        context=context,
        permission_manager=permission_manager,
        max_steps=settings.max_steps,
        temperature=settings.temperature,
        session_manager=session_mgr,
        artifact_manager=artifact_mgr,
        on_step_start=render_step_header,
        on_content_chunk=handle_content_chunk,
        on_thought_chunk=render_thought,
        on_tool_start=render_tool_start,
        on_tool_finish=render_tool_result,
        on_artifact_created=render_artifact_card,
        on_request_approval=request_tool_approval,
    )

    # Non-interactive mode
    if args.prompt:
        res = loop.step(args.prompt)
        console.print()
        sys.exit(0)

    # Interactive REPL mode
    print_welcome_banner(
        model_name=settings.model,
        cwd=str(target_cwd),
        git_status=get_git_summary(target_cwd),
        safe_mode=settings.auto_approve_safe_commands,
        session_id=session_mgr.session_id,
        skills_count=len(skill_mgr.skills)
    )

    start_repl(
        loop=loop,
        settings=settings,
        session_mgr=session_mgr,
        task_mgr=task_mgr,
        artifact_mgr=artifact_mgr,
        skill_mgr=skill_mgr
    )

if __name__ == "__main__":
    main()
