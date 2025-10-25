from functions.holding_functions import HoldingsManager
from tools.ticker import get_ticker
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt

def get_database_by_name(companies: list[str]) -> str:
    """
    To find/fetch hooldings by the name of company

    Args:
        companies: List of company names whose holdings we want to fetch extracted from the user prompt.
    """
    console = Console()
    manager = HoldingsManager()
    
    if not companies:
        console.print("[bold red]Error: No company names were provided.[/bold red]")
        return {"error": True}

    tickers_to_get = {}

    for company in companies:
        stock_list = get_ticker(company)

        if not stock_list:
            console.print(f"[bold red]Error: Ticker for company '{company}' not found![/bold red]")
            if len(companies) > 1:
                if not Confirm.ask("Do you want to continue with the other companies?", default=False):
                    console.print(f"[bold yellow]Operation cancelled by user.[/bold yellow]")
                    return "Operation cancelled by user."
                continue
            else:
                return f"Error: Ticker for company '{company}' not found!"

        selected_ticker = None

        if len(stock_list) > 1:
            table = Table(title=f"[bold]Multiple stocks found for '{company}'[/bold]", header_style="bold magenta")
            table.add_column("Option #", justify="center", style="cyan")
            table.add_column("Name", style="white")
            table.add_column("Symbol", style="green")
            table.add_column("Exchange", style="yellow")
            
            for i, stock in enumerate(stock_list, 1):
                name = stock.get("longname") or stock.get("shortname", "N/A")
                table.add_row(str(i), name, stock.get("symbol", "N/A"), stock.get("exchDisp", "N/A"))
            
            console.print(table)
            choice = IntPrompt.ask(
                "Input the number of the stock you want to view",
                choices=[str(i) for i in range(1, len(stock_list) + 1)],
                show_choices=False
            )
            selected_ticker = stock_list[choice - 1]["symbol"]
        else:
            selected_ticker = stock_list[0]["symbol"]

        if selected_ticker:
            tickers_to_get[company] = selected_ticker

    if not tickers_to_get:
        console.print("[yellow]No stocks were selected to view.[/yellow]")
        return "No stocks were selected to view."

    all_found_holdings = []
    for company, ticker in tickers_to_get.items():
        found_holdings = manager.get_holding_by_ticker(ticker=ticker)
        
        if not found_holdings:
            console.print(f"[yellow]No holdings found in your portfolio for ticker: {ticker}[/yellow]")
            continue

        console.print(f"[bold cyan]Displaying holdings for {ticker}:[/bold cyan]")
        for holding in found_holdings:
            details_table = Table.grid(padding=(0, 2))
            details_table.add_column(style="bold cyan")
            details_table.add_column()

            price = holding.get('price', 0)
            quantity = holding.get('quantity', 0)

            details_table.add_row("Name:", holding.get('name', 'N/A'))
            details_table.add_row("Ticker:", f"[green]{holding.get('ticker', 'N/A')}[/green]")
            details_table.add_row("Price:", f"[yellow]${price:,.2f}[/yellow]")
            details_table.add_row("Quantity:", f"[blue]{quantity}[/blue]")
            details_table.add_row("Transaction ID:", f"[dim]{holding.get('transaction_id', 'N/A')}[/dim]")

            display_panel = Panel(
                details_table,
                title=f"[bold]Holding Details: [white]{holding.get('name', '')}[/white][/bold]",
                border_style="cyan",
                padding=(1, 2)
            )
            console.print(display_panel)
            all_found_holdings.append(holding)

    return "All holdings have been displayed."
