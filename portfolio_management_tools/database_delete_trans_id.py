from functions.holding_functions import HoldingsManager
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.text import Text

def delete_database_by_trans(transaction_id: str) -> str:
    """
    Delete a holding using transaction ID from the users account

    Args:
        transaction: Transaction ID of the holding to delete extracted from the user prompt
    """
    console = Console()
    manager = HoldingsManager()

    if not transaction_id:
        console.print(f"[bold red]Error: Transaction ID was not provided.[/bold red]")
        return "Error: Transaction ID was not provided."

    holdings = manager.list_holdings()
    holding_to_delete = None

    for holding in holdings:
        if holding.get("transaction_id") == transaction_id:
            holding_to_delete = holding
            break
            
    if holding_to_delete:
        details = Text(justify="left")
        details.append("You are about to delete the following holding:\n\n", style="yellow")
        details.append(f"  Name: ", style="bold")
        details.append(f"{holding_to_delete.get('name', 'N/A')}\n")
        details.append(f"  Ticker: ", style="bold")
        details.append(f"{holding_to_delete.get('ticker', 'N/A')}\n")
        details.append(f"  Quantity: ", style="bold")
        details.append(f"{holding_to_delete.get('quantity', 'N/A')}\n")
        details.append(f"  Price: ", style="bold")
        details.append(f"{holding_to_delete.get('price', 'N/A')}\n")
        details.append(f"  Transaction ID: ", style="bold")
        details.append(f"{holding_to_delete.get('transaction_id', 'N/A')}")

        confirmation_panel = Panel(
            details,
            title="[bold red]Confirm Deletion[/bold red]",
            border_style="red",
            padding=(1, 2)
        )
        console.print(confirmation_panel)

        if Confirm.ask("Are you sure you want to proceed?", default=False):
            display = manager.delete_holding_by_transaction_id(transaction_id=transaction_id)
            console.print(f"[green]✔ {display}[/green]")
            return display
        else:
            display = "Deletion cancelled by user."
            console.print(f"[yellow]⚠ {display}[/yellow]")
            return "Deletion cancelled by user."

    else:
        display = f"Holding with Transaction ID '{transaction_id}' not found!"
        console.print(f"[bold red]Error: {display}[/bold red]")
        return f"Holding with Transaction ID '{transaction_id}' not found!"
