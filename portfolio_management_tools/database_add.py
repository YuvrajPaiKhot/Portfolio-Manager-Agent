from functions.holding_functions import HoldingsManager
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt
from tools.ticker import get_ticker
from tools.financials import get_summary_profile, get_additional_info, get_financial_data
import uuid
from datetime import datetime
from tools.ticker import get_tickers

def add_to_database(company: str, quantity: int, price: float) -> str:
    """
    Add new holdings in to users account

    Args:
        company: The company extracted from the prompt
        quantity: The quantity to add for the company extracted from the prompt
        price: The price to add for the company extracted from the prompt
    """

    if not company:
        console.print("[red]Error: No companies were found to add.[/red]")
        return "No companies were found to add."

    tickers = get_tickers([company])

    if not tickers:
        # console.print(f"[red]Error: Ticker for {company} not found.[/red]")
        return f"Error: Ticker for {company} not found."
    
    exchange, quoteType, longName, shortName = get_additional_info(tickers[company])
    sectorKey, industryKey = get_summary_profile(tickers[company])
    financial_data = get_financial_data(tickers[company])

    holding = {
        "name": longName if longName else shortName,
        "price": price,
        "quantity": quantity,
        "sector": sectorKey,
        "industry": industryKey,
        "ticker": tickers[company],
        "quoteType": quoteType,
        "transaction_id": str(uuid.uuid4()),
        "transaction_time": datetime.now().isoformat(),
        "currency": financial_data.get("financialCurrency", "NA"),
        "exchange": exchange
    }

    console = Console()
    manager = HoldingsManager()

    summary_table = Table(header_style="bold magenta", border_style="dim")
    summary_table.add_column("Name", style="white", no_wrap=True)
    summary_table.add_column("Ticker", style="green")
    summary_table.add_column("Quantity", justify="right", style="blue")
    summary_table.add_column("Price", justify="right", style="yellow")

    summary_table.add_row(
        holding["name"],
        holding["ticker"],
        str(holding["quantity"]),
        f"{holding["currency"]} {holding["price"]:,.2f}"
    )

    console.print(
        Panel(
            summary_table,
            title="[bold]Confirm New Holding[/bold]",
            border_style="green",
            padding=(1, 2)
        )
    )

    if not Confirm.ask("Do you want to add this holding to your portfolio?", default=True):
        console.print(f"[yellow]Operation cancelled by user. Holding for {company} wasn't added.[/yellow]")
        return f"Operation cancelled by user. Holding for {company} wasn't added."

    console.print("\nAdding holding...", style="dim italic")
    display = None
    display = manager.add_holding(holding)
    
    if not display:
        console.print(f"[bold red]There was a problem while adding the holding to your portfolio![/bold red]")
        return "There was a problem while adding the holding to your portfolio!"
    else:
        console.print(f"[green]✔ {display}[/green]")

    return display