from functions.holding_functions import HoldingsManager
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

def get_by_trans(transaction_id: str) -> str:
    """
    To find/fetch  holdings by their transaction ID

    Args:
        transaction: Transaction ID of the holding to fetch extracted from the user prompt.
    """
    manager = HoldingsManager()
    console = Console()

    if not transaction_id:
        error_msg = "Transaction ID was not provided."
        console.print(f"[bold red]Error: {error_msg}[/bold red]")
        return "Transaction ID was not provided."
    
    holding_to_get = manager.get_holding_by_transaction_id(transaction_id)

    if holding_to_get:
        details_table = Table.grid(padding=(0, 2))
        details_table.add_column(style="bold cyan")
        details_table.add_column()

        details_table.add_row("Name:", holding_to_get.get('name', 'N/A'))
        details_table.add_row("Ticker:", f"[green]{holding_to_get.get('ticker', 'N/A')}[/green]")
        
        price = holding_to_get.get('price', 0)
        quantity = holding_to_get.get('quantity', 0)

        details_table.add_row("Price:", f"[yellow]${price:,.2f}[/yellow]")
        details_table.add_row("Quantity:", f"[blue]{quantity}[/blue]")
        details_table.add_row("Transaction ID:", f"[dim]{holding_to_get.get('transaction_id', 'N/A')}[/dim]")

        display_panel = Panel(
            details_table,
            title=f"[bold]Holding Details: [white]{holding_to_get.get('name', '')}[/white][/bold]",
            border_style="cyan",
            padding=(1, 2)
        )
        
        console.print(display_panel)
        return "Holding displayed successfully"

    else:
        display = f"Holding with Transaction ID '{transaction_id}' not found!"
        console.print(f"[bold red]Error: {display}[/bold red]")
        return f"Holding with Transaction ID '{transaction_id}' not found!"
