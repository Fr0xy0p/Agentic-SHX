"""Rich console configuration, themes, and banners."""

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
   ___                    _   _         ___ _  ___  __
  / _ \                  | | (_)       / __| || \ \/ /
 / /_\ \ __ _  ___ _ __  | |_ _  ___   \__ \ __ |\  / 
 |  _  |/ _` |/ _ \ '_ \ | __| |/ __|  |___/_||_|/_/\_\
 | | | | (_| |  __/ | | || |_| | (__                   
 \_| |_/\__, |\___|_| |_| \__|_|\___|                  
         __/ |                                         
        |___/        Autonomous Terminal Coding Agent
"""

def print_welcome_banner(model_name: str, cwd: str, git_status: str, safe_mode: bool) -> None:
    """Displays the startup banner and session status card."""
    banner_text = Text(BANNER, style="bold cyan")
    console.print(banner_text)

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold white", justify="right")
    grid.add_column(style="dim cyan")

    grid.add_row("Model:", model_name)
    grid.add_row("Workspace:", cwd)
    grid.add_row("Git Branch:", git_status)
    grid.add_row("Safety Mode:", "[green]Auto-approve safe reads[/green]" if safe_mode else "[yellow]Ask all[/yellow]")

    panel = Panel(
        grid,
        title="[bold green]● Session Ready[/bold green]",
        subtitle="[dim]Type /help for slash commands | Ctrl+C to interrupt[/dim]",
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(panel)
    console.print()
