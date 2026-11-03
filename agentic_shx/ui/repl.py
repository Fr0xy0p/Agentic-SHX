"""Interactive REPL with prompt_toolkit and slash commands."""

import os
from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style

from agentic_shx.ui.console import console
from agentic_shx.agent.loop import AgentLoop
from agentic_shx.config import DEFAULT_HISTORY_PATH, Settings

SLASH_COMMANDS = [
    "/help",
    "/model",
    "/compact",
    "/clear",
    "/diff",
    "/status",
    "/tools",
    "/exit",
    "/quit",
]

prompt_style = Style.from_dict({
    "prompt": "#00d7d7 bold",
})

def handle_slash_command(command_str: str, loop: AgentLoop, settings: Settings) -> bool:
    """
    Handles local slash commands.
    Returns True if execution should continue, False to exit.
    """
    parts = command_str.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd in ("/exit", "/quit"):
        console.print("[yellow]Exiting Agentic-SHX. Happy coding![/yellow]")
        return False

    elif cmd == "/help":
        console.print("""
[bold cyan]Agentic-SHX Commands:[/bold cyan]
  [green]/help[/green]             Show this help menu
  [green]/model [name][/green]     View or switch the active LLM (e.g. /model claude-3-7-sonnet)
  [green]/diff[/green]             View current uncommitted git changes
  [green]/status[/green]           Show git branch, working directory, and token estimates
  [green]/compact[/green]          Compact message history to reduce token usage
  [green]/clear[/green]            Clear conversation history and start fresh
  [green]/tools[/green]            List all registered agent tools
  [green]/exit[/green] or [green]/quit[/green]     Exit the application

[bold cyan]Tips:[/bold cyan]
  • Press [bold]Enter[/bold] to submit prompt.
  • Press [bold]Ctrl+C[/bold] to interrupt model generation or cancel current line.
  • Press [bold]Ctrl+D[/bold] to exit.
""")

    elif cmd == "/model":
        if arg:
            from agentic_shx.providers.factory import get_provider
            try:
                new_provider = get_provider(
                    model=arg,
                    api_keys=settings.api_keys,
                    api_bases=settings.api_bases
                )
                loop.provider = new_provider
                settings.model = arg
                settings.save()
                console.print(f"[green]✓ Switched model to:[/green] [bold cyan]{arg}[/bold cyan]")
            except Exception as e:
                console.print(f"[bold red]Failed to switch model:[/bold red] {e}")
        else:
            console.print(f"Current active model: [bold cyan]{loop.provider.model}[/bold cyan]")

    elif cmd == "/diff":
        diff_tool = loop.tool_registry.get("git_diff")
        if diff_tool:
            res = diff_tool.execute()
            from agentic_shx.ui.renderers import render_tool_result
            from agentic_shx.providers.base import ToolCall
            dummy_tc = ToolCall(id="diff", name="git_diff", arguments={})
            render_tool_result(dummy_tc, res.output or res.error or "", res.success)
        else:
            console.print("[red]git_diff tool is not available.[/red]")

    elif cmd == "/status":
        from agentic_shx.agent.prompts import get_git_summary
        cwd = Path.cwd()
        console.print(f"Directory: [cyan]{cwd}[/cyan]")
        console.print(f"Git: [cyan]{get_git_summary(cwd)}[/cyan]")
        console.print(f"Model: [cyan]{loop.provider.model}[/cyan]")
        console.print(f"Estimated Context Tokens: [cyan]{loop.context.estimate_tokens():,}[/cyan]")

    elif cmd == "/compact":
        trimmed = loop.context.compact_history()
        console.print(f"[green]✓ History compacted. Pruned {trimmed} characters from older outputs.[/green]")

    elif cmd == "/clear":
        loop.context.clear()
        console.print("[green]✓ Conversation history cleared.[/green]")

    elif cmd == "/tools":
        console.print("[bold cyan]Available Tools:[/bold cyan]")
        for tool in loop.tool_registry.list_tools():
            console.print(f"  • [bold magenta]{tool.name}[/bold magenta]: [dim]{tool.description}[/dim]")

    else:
        console.print(f"[red]Unknown slash command:[/red] {cmd}. Type [green]/help[/green] for options.")

    return True


def start_repl(loop: AgentLoop, settings: Settings) -> None:
    """Launch the main interactive REPL."""
    DEFAULT_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    history = FileHistory(str(DEFAULT_HISTORY_PATH))
    completer = WordCompleter(SLASH_COMMANDS, ignore_case=True, match_middle=False)

    session = PromptSession(
        history=history,
        auto_suggest=AutoSuggestFromHistory(),
        completer=completer,
        style=prompt_style
    )

    while True:
        try:
            user_input = session.prompt([("class:prompt", "shx ❯ ")]).strip()
            if not user_input:
                continue

            # Check for slash commands
            if user_input.startswith("/"):
                should_continue = handle_slash_command(user_input, loop, settings)
                if not should_continue:
                    break
                continue

            # Execute autonomous agent turn
            console.print()
            final_response = loop.step(user_input)

            # If there was remaining response content that wasn't streamed chunk-by-chunk
            from agentic_shx.ui.renderers import render_markdown
            if final_response and not loop.on_content_chunk:
                render_markdown(final_response)
            console.print()

        except KeyboardInterrupt:
            console.print("\n[dim](Cancelled input)[/dim]")
            continue
        except EOFError:
            console.print("\n[yellow]Exiting Agentic-SHX.[/yellow]")
            break
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {str(e)}\n")

