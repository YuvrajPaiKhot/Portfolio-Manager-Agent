from functions.holding_functions import HoldingsManager
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm

def update_database(transaction_id: str, new_quantity: int = -1, new_price: float = -1) -> str:
    """
    Update a particular holding in user's account

    Args:
        transaction_id: The transaction ID of the holding to update
        new_quantity: The new quantity of the holding to update. Default is -1 (means unchanged).
        new_price: The new price of the holding to update. Default is -1 (means unchanged).is -1
    """
    manager = HoldingsManager()
    holdings = manager.list_holdings()
    console = Console()
    
    holding_to_update = None
    
    for holding in holdings:
        if holding["transaction_id"] == transaction_id:
            holding_to_update = holding
            break

    if holding_to_update:
        table = Table(show_header=True, header_style="bold magenta", expand=True)
        table.add_column("Attribute", justify="right", style="cyan", no_wrap=True)
        table.add_column("Current Value", justify="center", style="dim")
        table.add_column("New Value", justify="center", style="bold green")

        if new_quantity != -1:
            table.add_row(
                "Quantity",
                str(holding_to_update["quantity"]),
                str(new_quantity)
            )
        
        if new_price != -1:
            table.add_row(
                "Price",
                f"${holding_to_update['price']:.2f}",
                f"${new_price:.2f}"
            )

        confirmation_panel = Panel(
            table,
            title=f"Confirm Update for [bold]{holding_to_update['name']} ({holding_to_update['ticker']})[/bold]",
            border_style="yellow",
            padding=(1, 2)
        )
        
        console.print(confirmation_panel)

        if Confirm.ask("Do you want to apply these changes?", default=True):
            display = manager.update_holding(
                transaction_id=transaction_id, 
                updated_quantity=new_quantity, 
                updated_price=new_price
            )
            console.print(f"[green]✔ {display}[/green]")
            return "display"
        else:
            console.print("[yellow]⚠ Update cancelled by user.[/yellow]")
            return "Update operation cancelled by user."
    
    else:
        error_message = f"Could not find a holding with transaction ID: {transaction_id}"
        console.print(f"[bold red]Error: {error_message}[/bold red]")
        return f"Error: {error_message}"

