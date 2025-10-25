import yahooquery as yq
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm

def get_ticker(company_name):
    """
    Takes a company name (e.g., 'Apple') and returns its stock ticker symbol (e.g., 'AAPL').
    """
    data = yq.search(company_name, first_quote=False, news_count=0, quotes_count=15)

    return data.get("quotes", [])


def get_tickers(companies):
    """
    Extracts company tickers, presents them in a rich table,
    and prompts the user for a selection.
    """
    console = Console()
    console.print("Extracting tickers...", style="dim italic", )

    tickers = {}

    for company in companies:
        stock_list = get_ticker(company)

        if not stock_list:
            console.print(f"[bold red]Ticker for company '{company}' not found![/bold red]")
            if len(companies) == 1 or (companies.index(company) == len(companies)-1 and not tickers):
                return {}
            else:
                if not Prompt.ask(f"Could not find '{company}'. Continue with other companies?", choices=["y", "n"], default="y") == "y":
                    return {}
                continue

        table = Table(title=f"Found Tickers for [bold cyan]{company}[/bold cyan]", show_header=True, header_style="bold magenta")
        table.add_column("Option #", style="dim", width=10, justify="center")
        table.add_column("Name", style="cyan")
        table.add_column("Symbol", style="green")
        table.add_column("Exchange", style="yellow")
        table.add_column("Type", style="blue")

        for i, stock in enumerate(stock_list, 1):
            name = stock.get("longname") or stock.get("shortname", "N/A")
            symbol = stock.get("symbol", "N/A")
            exchange = stock.get("exchDisp", "N/A")
            quote_type = stock.get("quoteType", "N/A")
            table.add_row(str(i), name, symbol, exchange, quote_type)

        console.print(table)

        if(len(stock_list) > 1):
            chosen_index = IntPrompt.ask(
                "Please enter the number of the stock",
                choices=[str(i) for i in range(1, len(stock_list) + 1)],
                show_choices=False
            )

            selected_symbol = stock_list[chosen_index - 1]["symbol"]
            tickers[company] = selected_symbol
        else:
            choice = Confirm.ask(
                "Is this the stock you want to analyze? (Y/N)",
                choices=["y", "n", "Y", "N"],
                show_choices=False
            )

            if (choice == True):
                selected_symbol = stock_list[0]["symbol"]
                tickers[company] = selected_symbol
            else:
                console.print("[bold yellow]User cancelled operation![/bold yellow]")
                return {}
            
        console.print(f"You selected: [bold green]{selected_symbol}[/bold green]\n")

    return tickers
