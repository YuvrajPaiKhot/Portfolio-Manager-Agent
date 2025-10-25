from functions.holding_functions import HoldingsManager
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.text import Text

def clear_database() -> str:
    """
    Clear all holdings from the users account
    """
    console = Console()
    manager = HoldingsManager()

    warning_text = Text(justify="center")
    warning_text.append("You are about to ", style="yellow")
    warning_text.append("permanently delete all holdings", style="bold red underline")
    warning_text.append(" from the database.\n\nThis action cannot be undone.", style="yellow")

    warning_panel = Panel(
        warning_text,
        title="[bold red] DANGER ZONE [/bold red]",
        border_style="red",
        padding=(1, 2)
    )
    
    console.print(warning_panel)

    if Confirm.ask("Are you absolutely sure you want to proceed?", default=False):
        display = manager.clear_all_holdings()
        console.print(f"[bold green]✔ All holdings have been successfully cleared.[/bold green]")
        return "All holdings have been successfully cleared"
    else:
        display = "Holdings were not cleared."
        console.print(f"[yellow]⚠ Operation cancelled by user.[/yellow]")
        return "Operation cancelled by user."
