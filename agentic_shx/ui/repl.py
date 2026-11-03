"""Interactive Antigravity-style REPL with slash commands and autocompletion."""

import os
from pathlib import Path
from typing import Optional
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style

from agentic_shx.ui.console import console
from agentic_shx.agent.loop import AgentLoop
from agentic_shx.config import DEFAULT_HISTORY_PATH, Settings
from agentic_shx.session.manager import SessionManager
from agentic_shx.tasks.manager import TaskManager
from agentic_shx.artifacts.manager import ArtifactManager
from agentic_shx.skills.manager import SkillManager
from agentic_shx.ui.renderers import render_markdown, render_tool_result
from agentic_shx.providers.base import ToolCall

SLASH_COMMANDS = [
    "/help",
    "/goal",
    "/plan",
    "/tasks",
    "/artifacts",
    "/skills",
    "/model",
    "/diff",
    "/status",
    "/compact",
    "/clear",
    "/resume",
    "/tools",
    "/exit",
    "/quit",
]

prompt_style = Style.from_dict({
    "prompt": "#00d7d7 bold",
    "session": "#5f87af",
})

def handle_slash_command(
    command_str: str,
    loop: AgentLoop,
    settings: Settings,
    session_mgr: SessionManager,
    task_mgr: Optional[TaskManager] = None,
    artifact_mgr: Optional[ArtifactManager] = None,
    skill_mgr: Optional[SkillManager] = None
) -> bool:
    """Handles Antigravity slash commands. Returns False to exit, True to continue."""
    parts = command_str.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd in ("/exit", "/quit"):
        console.print("[yellow]Exiting Agentic-SHX. Session saved.[/yellow]")
        return False

    elif cmd == "/help":
        console.print("""
[bold cyan]Antigravity Slash Commands:[/bold cyan]
  [green]/goal <task>[/green]        Run a long-running, thorough autonomous goal without stopping
  [green]/plan[/green]               Direct agent to draft a multi-phase implementation artifact plan
  [green]/tasks[/green]              Inspect running background processes and daemon servers
  [green]/artifacts[/green]          List all structured markdown artifacts in this session
  [green]/skills[/green]             Browse specialized skills discovered in workspace
  [green]/diff[/green]               View current uncommitted git changes with colorized diff
  [green]/model [name][/green]      Switch active LLM dynamically (e.g. /model groq/llama-3.3-70b-versatile)
  [green]/status[/green]             View session ID, branch, tokens, and active components
  [green]/compact[/green]            Prune older tool observations to conserve token context
  [green]/clear[/green]              Clear in-memory trajectory and start fresh turn
  [green]/resume [id][/green]        List past sessions or switch to a previous conversation
  [green]/tools[/green]              Inspect all available tools and parameter signatures
  [green]/exit[/green] or [green]/quit[/green]      Exit session
""")

    elif cmd == "/goal":
        if not arg:
            console.print("[yellow]Usage: /goal <detailed description of the goal>[/yellow]")
        else:
            goal_prompt = (
                f"[HIGH-PRIORITY LONG-RUNNING AUTONOMOUS GOAL]\n{arg}\n\n"
                "INSTRUCTIONS: Be extra thorough. Investigate thoroughly, write or edit all necessary code, "
                "run build/test commands, and do not stop until the goal is fully accomplished and verified."
            )
            console.print(f"[bold green]🎯 Launching Autonomous Goal:[/bold green] {arg}\n")
            loop.max_steps = 50
            final_resp = loop.step(goal_prompt)
            if final_resp and not loop.on_content_chunk:
                render_markdown(final_resp)

    elif cmd == "/plan":
        plan_prompt = (
            "Please create a comprehensive implementation plan for our current objective using the `create_artifact` tool. "
            "Structure it with Phases, Architectural decisions, File modifications, Verification steps, and set request_feedback=true."
        )
        console.print("[bold cyan]📋 Requesting Implementation Plan Artifact...[/bold cyan]\n")
        final_resp = loop.step(plan_prompt)
        if final_resp and not loop.on_content_chunk:
            render_markdown(final_resp)

    elif cmd == "/tasks":
        if task_mgr:
            console.print(task_mgr.list_tasks())
        else:
            console.print("[dim]TaskManager is not active in this session.[/dim]")

    elif cmd == "/artifacts":
        if artifact_mgr:
            arts = artifact_mgr.list_artifacts()
            if not arts:
                console.print("[dim]No artifacts created in this session yet.[/dim]")
            else:
                console.print(f"[bold cyan]Artifacts ({len(arts)}):[/bold cyan]")
                for a in arts:
                    console.print(f"  • [bold white]{a.title}[/bold white] ([dim]{a.filename}[/dim]) -> {a.path}")
        else:
            console.print("[dim]ArtifactManager is not active.[/dim]")

    elif cmd == "/skills":
        if skill_mgr:
            skills = skill_mgr.list_skills()
            if not skills:
                console.print("[dim]No specialized skills discovered in workspace or global dir.[/dim]")
            else:
                console.print(f"[bold cyan]Discovered Skills ({len(skills)}):[/bold cyan]")
                for s in skills:
                    console.print(f"  • [bold magenta]{s.name}[/bold magenta]: [dim]{s.description}[/dim] ({s.path})")
        else:
            console.print("[dim]SkillManager is not active.[/dim]")

    elif cmd == "/diff":
        diff_tool = loop.tool_registry.get("git_diff")
        if diff_tool:
            res = diff_tool.execute()
            dummy_tc = ToolCall(id="diff", name="git_diff", arguments={})
            render_tool_result(dummy_tc, res.output or res.error or "", res.success)
        else:
            console.print("[red]git_diff tool is not available.[/red]")

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
            console.print(f"Current model: [bold cyan]{loop.provider.model}[/bold cyan]")

    elif cmd == "/status":
        from agentic_shx.agent.prompts import get_git_summary
        cwd = Path.cwd()
        console.print(f"Session ID: [bold green]{session_mgr.session_id}[/bold green]")
        console.print(f"Directory: [cyan]{cwd}[/cyan]")
        console.print(f"Git: [cyan]{get_git_summary(cwd)}[/cyan]")
        console.print(f"Model: [cyan]{loop.provider.model}[/cyan]")
        console.print(f"Estimated Tokens: [cyan]{loop.context.estimate_tokens():,}[/cyan]")

    elif cmd == "/compact":
        trimmed = loop.context.compact_history()
        console.print(f"[green]✓ History compacted. Pruned {trimmed} characters from older observations.[/green]")

    elif cmd == "/clear":
        loop.context.clear()
        console.print("[green]✓ Context trajectory cleared.[/green]")

    elif cmd == "/resume":
        sessions = SessionManager.list_all_sessions()
        if not sessions:
            console.print("[dim]No past sessions found to resume.[/dim]")
        else:
            console.print("[bold cyan]Recent Sessions:[/bold cyan]")
            for s in sessions[:10]:
                console.print(f"  • [bold green]{s.get('id')}[/bold green] | {s.get('title', 'Untitled')} | [dim]{s.get('created_at', '')[:16]}[/dim]")
            console.print("\nTo launch into a session, run: [bold cyan]shx -r <session_id>[/bold cyan]")

    elif cmd == "/tools":
        console.print("[bold cyan]Registered Tools:[/bold cyan]")
        for tool in loop.tool_registry.list_tools():
            console.print(f"  • [bold magenta]{tool.name}[/bold magenta]: [dim]{tool.description}[/dim]")

    else:
        console.print(f"[red]Unknown slash command:[/red] {cmd}. Type [green]/help[/green] for available commands.")

    return True


def start_repl(
    loop: AgentLoop,
    settings: Settings,
    session_mgr: SessionManager,
    task_mgr: Optional[TaskManager] = None,
    artifact_mgr: Optional[ArtifactManager] = None,
    skill_mgr: Optional[SkillManager] = None
) -> None:
    """Launch the interactive REPL loop."""
    DEFAULT_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    history = FileHistory(str(DEFAULT_HISTORY_PATH))
    completer = WordCompleter(SLASH_COMMANDS, ignore_case=True, match_middle=False)

    session = PromptSession(
        history=history,
        auto_suggest=AutoSuggestFromHistory(),
        completer=completer,
        style=prompt_style
    )

    prompt_tokens = [
        ("class:session", f"({session_mgr.session_id}) "),
        ("class:prompt", "shx ❯ ")
    ]

    while True:
        try:
            user_input = session.prompt(prompt_tokens).strip()
            if not user_input:
                continue

            # Record user input in session transcript
            session_mgr.log_event("USER_INPUT", user_input)
            session_mgr.set_title_from_prompt(user_input)

            # Check for slash command
            if user_input.startswith("/"):
                should_continue = handle_slash_command(
                    user_input, loop, settings, session_mgr, task_mgr, artifact_mgr, skill_mgr
                )
                if not should_continue:
                    break
                continue

            console.print()
            final_response = loop.step(user_input)

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
