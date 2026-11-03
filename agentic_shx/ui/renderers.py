"""Renderers for markdown, thinking process, tool cards, and artifacts."""

from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.text import Text
from rich.rule import Rule
from agentic_shx.ui.console import console
from agentic_shx.providers.base import ToolCall
from agentic_shx.artifacts.manager import Artifact

def render_markdown(text: str) -> None:
    """Render markdown block nicely."""
    if not text.strip():
        return
    md = Markdown(text)
    console.print(md)

def render_step_header(step_num: int, max_steps: int) -> None:
    """Print Antigravity-style step separator."""
    console.print(Rule(f"[bold cyan]Step {step_num}/{max_steps}[/bold cyan]", style="dim cyan"))

def render_thought(text: str) -> None:
    """Render model reasoning/thinking in styled container."""
    if not text.strip():
        return
    lines = text.strip().splitlines()
    preview = "\n".join(lines[:12])
    if len(lines) > 12:
        preview += f"\n... [dim](+{len(lines) - 12} more lines)[/dim]"
        
    panel = Panel(
        Text(preview, style="italic dim"),
        title="[bold yellow]🧠 Thinking / Plan[/bold yellow]",
        border_style="dim yellow",
        padding=(0, 1)
    )
    console.print(panel)

def render_tool_start(tool_call: ToolCall) -> None:
    """Display initiated tool invocation."""
    args_preview = []
    for k, v in tool_call.arguments.items():
        v_str = str(v)
        if len(v_str) > 60:
            v_str = v_str[:57] + "..."
        args_preview.append(f"{k}={v_str}")
    
    args_str = ", ".join(args_preview)
    console.print(f"[bold magenta]⚡ Tool Call:[/bold magenta] [bold cyan]{tool_call.name}[/bold cyan]({args_str})")

def render_tool_result(tool_call: ToolCall, output: str, success: bool) -> None:
    """Display the result of a tool execution in a styled Antigravity card."""
    border_style = "green" if success else "red"
    title_text = f"[bold green]✓ {tool_call.name}[/bold green]" if success else f"[bold red]✗ {tool_call.name} (Failed)[/bold red]"

    content = output.strip()
    if not content:
        content = "(no output)"

    # If it's a diff, render syntax highlighting
    if tool_call.name in ("git_diff", "diff") and ("@@" in content or content.startswith("diff ")):
        renderable = Syntax(content, "diff", theme="monokai", line_numbers=False)
    elif len(content.splitlines()) > 15:
        lines = content.splitlines()
        truncated_view = "\n".join(lines[:12]) + f"\n\n[dim]... (+{len(lines) - 12} more lines) ...[/dim]"
        renderable = Text(truncated_view)
    else:
        renderable = Text(content)

    panel = Panel(
        renderable,
        title=title_text,
        border_style=border_style,
        padding=(0, 1)
    )
    console.print(panel)
    console.print()

def render_artifact_card(artifact: Artifact) -> None:
    """Displays a prominent artifact card."""
    body = Text()
    body.append(f"Title: {artifact.title}\n", style="bold white")
    body.append(f"Location: {artifact.path}\n", style="dim cyan")
    if artifact.summary:
        body.append(f"Summary: {artifact.summary}\n", style="italic")
    if artifact.request_feedback:
        body.append("\n⚠️ User Feedback / Approval Requested on this plan.", style="bold yellow")

    panel = Panel(
        body,
        title="[bold cyan]📄 Artifact Created[/bold cyan]",
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(panel)

def render_subagent_event(sub_id: str, message: str) -> None:
    """Displays subagent lifecycle events."""
    console.print(f"[bold blue]🤖 [{sub_id}]:[/bold blue] {message}")
