from functions.holding_functions import HoldingsManager
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

def list_database() -> str:
    """
    List/View all the holdings in the user's account.
    """
    console = Console()
    manager = HoldingsManager()
    holdings = manager.list_holdings()

    if not holdings:
        empty_message = Text("Your portfolio is currently empty.", justify="center")
        panel = Panel(
            empty_message,
            title="[bold yellow]Portfolio Holdings[/bold yellow]",
            border_style="yellow",
            padding=(1, 2)
        )
        console.print(panel)
        return "No holdings to display."

    table = Table(
        title="[bold]Portfolio Holdings[/bold]",
        header_style="bold magenta",
        show_footer=True,
        footer_style="bold"
    )

    table.add_column("Transaction ID", justify="left", style="cyan", no_wrap=True, footer="Total Value")
    table.add_column("Name", style="white")
    table.add_column("Ticker", style="green")
    table.add_column("Price", justify="right", style="yellow")
    table.add_column("Quantity", justify="right", style="blue")
    table.add_column("Total Value", justify="right", style="bold green")

    total_portfolio_value = 0

    for holding in holdings:
        price = holding.get("price", 0)
        quantity = holding.get("quantity", 0)
        total_value = price * quantity
        total_portfolio_value += total_value
        
        table.add_row(
            holding.get("transaction_id", "N/A"),
            holding.get("name", "N/A"),
            holding.get("ticker", "N/A"),
            f"${price:,.2f}",
            str(quantity),
            f"${total_value:,.2f}"
        )

    table.columns[-1].footer = f"${total_portfolio_value:,.2f}"
    
    console.print(table)

    return "All holdings displayed successfully."
