"""Rich console themes, Antigravity-style headers and banners."""

from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "danger": "bold red",
    "success": "bold green",
    "tool.name": "bold magenta",
    "tool.arg": "dim cyan",
    "dim": "dim",
})

console = Console(theme=custom_theme)

BANNER = r"""
     _                    _   _         ___ _  ___  __
    / \   __ _  ___ _ __ | |_(_) ___   / __| || \ \/ /
   / _ \ / _` |/ _ \ '_ \| __| |/ __|  \__ \ __ |\  / 
  / ___ \ (_| |  __/ | | | |_| | (__   |___/_||_|/_/\_\
 /_/   \_\__, |\___|_| |_|\__|_|\___|                  
         |___/          Autonomous Terminal Coding Agent
"""

def print_welcome_banner(
    model_name: str,
    cwd: str,
    git_status: str,
    safe_mode: bool,
    session_id: str,
    skills_count: int = 0
) -> None:
    """Displays Antigravity-style startup banner and session card."""
    banner_text = Text(BANNER, style="bold cyan")
    console.print(banner_text)

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold white", justify="right")
    grid.add_column(style="dim cyan")

    grid.add_row("Session ID:", f"[bold green]{session_id}[/bold green]")
    grid.add_row("Active Model:", f"[bold yellow]{model_name}[/bold yellow]")
    grid.add_row("Workspace:", cwd)
    grid.add_row("Git Branch:", git_status)
    grid.add_row("Skills Loaded:", f"[cyan]{skills_count} specialized skills[/cyan]" if skills_count else "[dim]None[/dim]")
    grid.add_row(
        "Sandbox / Safety:",
        "[green]Auto-approve safe reads[/green]" if safe_mode else "[yellow]Ask all permissions[/yellow]"
    )

    panel = Panel(
        grid,
        title="[bold green]● Antigravity Runtime Ready[/bold green]",
        subtitle="[dim]Type /help for slash commands | Ctrl+C to interrupt | /goal for autonomous runs[/dim]",
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(panel)
    console.print()
