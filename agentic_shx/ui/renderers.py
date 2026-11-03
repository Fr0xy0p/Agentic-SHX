"""Renderers for markdown, tools, and code diffs."""

from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.text import Text
from agentic_shx.ui.console import console
from agentic_shx.providers.base import ToolCall

def render_markdown(text: str) -> None:
    """Render markdown block nicely."""
    if not text.strip():
        return
    md = Markdown(text)
    console.print(md)

def render_thought(text: str) -> None:
    """Render thinking/reasoning process in dim text."""
    if not text.strip():
        return
    panel = Panel(
        Text(text.strip(), style="dim italic"),
        title="[dim]Reasoning[/dim]",
        border_style="dim",
        padding=(0, 1)
    )
    console.print(panel)

def render_tool_start(tool_call: ToolCall) -> None:
    """Display that a tool execution is initiating."""
    args_preview = []
    for k, v in tool_call.arguments.items():
        v_str = str(v)
        if len(v_str) > 60:
            v_str = v_str[:57] + "..."
        args_preview.append(f"{k}={v_str}")
    
    args_str = ", ".join(args_preview)
    console.print(f"[bold magenta]⚡ Executing:[/bold magenta] [cyan]{tool_call.name}[/cyan]({args_str})")

def render_tool_result(tool_call: ToolCall, output: str, success: bool) -> None:
    """Display the result of a tool execution in a styled panel."""
    border_style = "green" if success else "red"
    title_text = f"[bold green]✓ {tool_call.name}[/bold green]" if success else f"[bold red]✗ {tool_call.name} (Failed)[/bold red]"

    content = output.strip()
    if not content:
        content = "(no output)"

    # If it's a git diff or unified diff, render with diff syntax highlighting
    if tool_call.name in ("git_diff", "diff") and ("@@" in content or content.startswith("diff ")):
        renderable = Syntax(content, "diff", theme="monokai", line_numbers=False)
    elif len(content.splitlines()) > 15:
        # Truncate preview in UI if very tall
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
