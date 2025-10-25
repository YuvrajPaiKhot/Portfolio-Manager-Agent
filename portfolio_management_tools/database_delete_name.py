from functions.holding_functions import HoldingsManager
from tools.ticker import get_ticker
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt

def delete_database_by_name(companies: list[str]) -> str:
    """
    Delete a holding by name from the users account

    Args:
        companies: List of companies to delete, extracted from the user prompt.
    """
    console = Console()
    manager = HoldingsManager()
    
    if not companies:
        console.print("[bold red]Error: No company names were provided for deletion.[/bold red]")
        return "Error: No company names were provided for deletion."

    tickers_to_delete = {}

    for company in companies:
        stock_list = get_ticker(company)

        if not stock_list:
            console.print(f"[bold red]Error: Ticker for company '{company}' not found![/bold red]")
            if len(companies) > 1:
                if not Confirm.ask("Do you want to continue with the other companies?", default=False):
                    console.print(f"[bold yellow]Deletion cancelled by user.[/bold yellow]")
                    return "Deletion cancelled by user."
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
                "Input the number of the stock you want to delete",
                choices=[str(i) for i in range(1, len(stock_list) + 1)],
                show_choices=False
            )
            selected_ticker = stock_list[choice - 1]["symbol"]
        
        else:
            stock = stock_list[0]
            name = stock.get("longname") or stock.get("shortname", "N/A")
            
            details_panel = Panel(
                f"[bold]Name:[/bold] {name}\n"
                f"[bold]Symbol:[/bold] [green]{stock.get('symbol', 'N/A')}[/green]\n"
                f"[bold]Exchange:[/bold] [yellow]{stock.get('exchDisp', 'N/A')}[/yellow]",
                title=f"[bold red]Confirm Deletion for '{company}'[/bold red]",
                border_style="red",
                padding=(1, 2)
            )
            console.print(details_panel)
            if Confirm.ask("Are you sure you want to delete this stock?", default=False):
                selected_ticker = stock["symbol"]

        if selected_ticker:
            tickers_to_delete[company] = selected_ticker

    if not tickers_to_delete:
        console.print("[yellow]No holdings were selected for deletion.[/yellow]")
        return {"error": False}

    final_display_messages = []
    for company, ticker in tickers_to_delete.items():
        result_message = manager.delete_holding_by_ticker(ticker=ticker)
        console.print(f"[green]{result_message}[/green]")
        final_display_messages.append(result_message)

    return {"error": False}
