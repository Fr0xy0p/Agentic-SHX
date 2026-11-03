"""Interactive user approval dialog for permissions."""

from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from agentic_shx.ui.console import console
from agentic_shx.safety.permissions import ApprovalChoice, RiskLevel

def request_tool_approval(
    tool_name: str,
    arguments: dict,
    risk_level: RiskLevel,
    reason: str
) -> ApprovalChoice:
    """Prompts the user interactively before running potentially dangerous or modifying tools."""
    risk_color = "red" if risk_level == RiskLevel.DANGEROUS else "yellow"
    
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold white", justify="right")
    table.add_column()

    table.add_row("Tool:", f"[cyan]{tool_name}[/cyan]")
    for k, v in arguments.items():
        v_str = str(v)
        if len(v_str) > 100:
            v_str = v_str[:97] + "..."
        table.add_row(f"{k}:", f"[yellow]{v_str}[/yellow]")
    table.add_row("Risk Level:", f"[{risk_color}]{risk_level.value}[/{risk_color}]")
    table.add_row("Reason:", f"[dim]{reason}[/dim]")

    panel = Panel(
        table,
        title=f"[{risk_color}]⚠️ Permission Required[/{risk_color}]",
        border_style=risk_color,
        padding=(1, 2)
    )
    console.print(panel)

    prompt_choices = "[bold cyan](y)[/bold cyan]es / [bold cyan](a)[/bold cyan]lways allow / [bold red](n)[/bold red]o / a[bold red](b)[/bold red]ort"
    choice = Prompt.ask(
        f"Allow execution? {prompt_choices}",
        choices=["y", "yes", "a", "always", "n", "no", "b", "abort"],
        default="y"
    ).lower()

    if choice in ("y", "yes"):
        return ApprovalChoice.YES
    elif choice in ("a", "always"):
        return ApprovalChoice.ALWAYS
    elif choice in ("b", "abort"):
        return ApprovalChoice.ABORT
    else:
        return ApprovalChoice.NO

