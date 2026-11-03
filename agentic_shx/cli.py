"""CLI Entrypoint for Agentic-SHX."""

import sys
import argparse
from pathlib import Path

from agentic_shx import __version__
from agentic_shx.config import Settings
from agentic_shx.providers.factory import get_provider
from agentic_shx.tools.registry import ToolRegistry
from agentic_shx.safety.permissions import PermissionManager
from agentic_shx.agent.prompts import build_system_prompt, get_git_summary
from agentic_shx.agent.context import ConversationContext
from agentic_shx.agent.loop import AgentLoop
from agentic_shx.ui.console import console, print_welcome_banner
from agentic_shx.ui.renderers import (
    render_markdown,
    render_thought,
    render_tool_start,
    render_tool_result
)
from agentic_shx.ui.approval import request_tool_approval
from agentic_shx.ui.repl import start_repl

def main() -> None:
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
        help="Override active LLM model (e.g. gemini/gemini-2.5-flash, claude-3-7-sonnet, gpt-4o, ollama/qwen2.5-coder)."
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
        console.print("[dim]Set your API key via environment variable (e.g. GEMINI_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY).[/dim]")
        sys.exit(1)

    # Initialize Tools and Safety
    tool_registry = ToolRegistry.create_default(cwd=str(target_cwd))
    permission_manager = PermissionManager(
        auto_approve_safe=settings.auto_approve_safe_commands
    )

    # Initialize System Context
    system_prompt = build_system_prompt(cwd=target_cwd)
    context = ConversationContext(system_prompt=system_prompt)

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
        on_content_chunk=handle_content_chunk,
        on_thought_chunk=render_thought,
        on_tool_start=render_tool_start,
        on_tool_finish=render_tool_result,
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
        safe_mode=settings.auto_approve_safe_commands
    )

    start_repl(loop, settings)

if __name__ == "__main__":
    main()
