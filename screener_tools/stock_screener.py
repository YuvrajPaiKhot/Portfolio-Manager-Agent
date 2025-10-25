from typing import List, Literal, Dict, Any
from yfinance import EquityQuery
from yfinance import FundQuery
from rich.console import Console
from yahooquery import Screener
import yfinance as yf
from rich.panel import Panel
from rich.table import Table
from datetime import datetime
from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated
from tools.any_prompt import display_result_for_unknown_prompts
from mappings import screener_fields_needing_conversion, country_to_currency
from currency_converter import CurrencyConverter 

def display_predefined_screener_results(screener_name: str, list_of_quotes: list):
    """
    Takes the name of a screener and a list of quote dictionaries and displays
    the results in a beautifully formatted table using the rich library.

    Args:
        screener_name: The name of the predefined screener that was run (e.g., 'Most Actives').
        list_of_quotes: A list of dictionary objects, where each dictionary is a quote.
    """
    console = Console()

    if not list_of_quotes:
        console.print(Panel(f"No results found for the '{screener_name}' screener.", style="dim"))
        return

    table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="dim"
    )
    table.add_column("Symbol", style="bold yellow", width=12)
    table.add_column("Company Name", style="white", min_width=20, max_width=35)
    table.add_column("Price (USD)", justify="right", style="bold")
    table.add_column("% Change", justify="right")
    table.add_column("Market Cap", justify="right")
    table.add_column("Forward P/E", justify="right")
    table.add_column("P/B Ratio", justify="right")
    table.add_column("Volume", justify="right")

    for quote in list_of_quotes:
        def get(key, default="N/A"):
            return quote.get(key, default)

        symbol = get('symbol')
        name = get('shortName', get('longName', 'N/A'))
        price = get('regularMarketPrice')
        change_pct = get('regularMarketChangePercent')
        market_cap = get('marketCap')
        forward_pe = get('forwardPE')
        price_to_book = get('priceToBook')
        volume = get('regularMarketVolume')
        currency = get('financialCurrency', 'USD')

        price_str = f"{currency} {price:.2f}" if isinstance(price, (int, float)) else "N/A"
        
        if isinstance(change_pct, (int, float)):
            change_str = f"[{'green' if change_pct >= 0 else 'red'}]{change_pct:+.2f}%[/{'green' if change_pct >= 0 else 'red'}]"
        else:
            change_str = "N/A"
            
        market_cap_str = f"{market_cap / 1_000_000_000:.2f}B" if isinstance(market_cap, (int, float)) else "N/A"
        volume_str = f"{volume / 1_000_000:.2f}M" if isinstance(volume, (int, float)) else "N/A"
        
        pe_str = f"{forward_pe:.2f}" if isinstance(forward_pe, (int, float)) else "N/A"
        pb_str = f"{price_to_book:.2f}" if isinstance(price_to_book, (int, float)) else "N/A"

        table.add_row(
            symbol,
            name,
            price_str,
            change_str,
            market_cap_str,
            pe_str,
            pb_str,
            volume_str
        )

    screener_title = screener_name.replace("_", " ").title()
    
    main_panel = Panel(
        table,
        title=f"[bold magenta]Screener Results: {screener_title}[/bold magenta]",
        border_style="magenta",
        padding=(1, 1),
        subtitle=f"[dim]Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]"
    )

    console.print(main_panel)



def display_fund_screener_results(list_of_quotes: list):
    """
    Takes a list of fund quote dictionaries and displays the results in a 
    beautifully formatted table using the rich library.

    Args:
        list_of_quotes: A list of dictionary objects, where each is a fund quote.
    """
    console = Console()

    if not list_of_quotes:
        console.print(Panel("No fund results found for the screener.", style="dim"))
        return

    table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="dim"
    )
    table.add_column("Symbol", style="bold yellow", width=12)
    table.add_column("Fund Name", style="white", min_width=20, max_width=40)
    table.add_column("Price (NAV)", justify="right", style="bold")
    table.add_column("% Change", justify="right")
    table.add_column("Net Assets", justify="right")
    table.add_column("Expense Ratio", justify="right")
    table.add_column("YTD Return", justify="right")
    table.add_column("Trailing P/E", justify="right")

    for quote in list_of_quotes:
        def get(key, default="N/A"):
            return quote.get(key, default)

        symbol = get('symbol')
        name = get('shortName', get('longName', 'N/A'))
        price = get('regularMarketPrice')
        change_pct = get('regularMarketChangePercent')
        net_assets = get('netAssets')
        expense_ratio = get('netExpenseRatio')
        ytd_return = get('ytdReturn')
        trailing_pe = get('trailingPE')
        currency = get('financialCurrency', 'USD')

        price_str = f"{currency} {price:.2f}" if isinstance(price, (int, float)) else "N/A"
        
        if isinstance(change_pct, (int, float)):
            change_str = f"[{'green' if change_pct >= 0 else 'red'}]{change_pct:+.2f}%[/{'green' if change_pct >= 0 else 'red'}]"
        else:
            change_str = "N/A"
            
        if isinstance(net_assets, (int, float)):
            if net_assets >= 1_000_000_000_000:
                assets_str = f"${net_assets / 1_000_000_000_000:.2f}T"
            else:
                assets_str = f"${net_assets / 1_000_000_000:.2f}B"
        else:
            assets_str = "N/A"

        expense_str = f"{expense_ratio * 100:.2f}%" if isinstance(expense_ratio, (int, float)) else "N/A"
        ytd_return_str = f"{ytd_return:.2f}%" if isinstance(ytd_return, (int, float)) else "N/A"
        pe_str = f"{trailing_pe:.2f}" if isinstance(trailing_pe, (int, float)) else "N/A"

        table.add_row(
            symbol,
            name,
            price_str,
            change_str,
            assets_str,
            expense_str,
            ytd_return_str,
            pe_str
        )

    main_panel = Panel(
        table,
        title="[bold magenta]Fund Screener Results[/bold magenta]",
        border_style="magenta",
        padding=(1, 1),
        subtitle=f"[dim]Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]"
    )

    console.print(main_panel)




def display_equity_screener_results(list_of_quotes: list):
    """
    Takes a list of equity quote dictionaries and displays the results in a
    beautifully formatted table using the rich library.

    Args:
        list_of_quotes: A list of dictionary objects, where each is an equity quote.
    """
    console = Console()

    if not list_of_quotes:
        console.print(Panel("No equity results found for the screener.", style="dim"))
        return

    table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="dim"
    )
    table.add_column("Symbol", style="bold yellow", width=12)
    table.add_column("Company Name", style="white", min_width=20, max_width=35)
    table.add_column("Price", justify="right", style="bold")
    table.add_column("% Change", justify="right")
    table.add_column("Market Cap", justify="right")
    table.add_column("Trailing P/E", justify="right")
    table.add_column("P/B Ratio", justify="right")
    table.add_column("Volume", justify="right")

    for quote in list_of_quotes:
        def get(key, default="N/A"):
            return quote.get(key, default)

        symbol = get('symbol')
        name = get('shortName', get('longName', 'N/A'))
        price = get('regularMarketPrice')
        change_pct = get('regularMarketChangePercent')
        market_cap = get('marketCap')
        trailing_pe = get('trailingPE')
        price_to_book = get('priceToBook')
        volume = get('regularMarketVolume')
        currency = get('financialCurrency', 'USD')

        
        price_str = f"{currency} {price:,.2f}" if isinstance(price, (int, float)) else "N/A"
        
        if isinstance(change_pct, (int, float)):
            change_str = f"[{'green' if change_pct >= 0 else 'red'}]{change_pct:+.2f}%[/{'green' if change_pct >= 0 else 'red'}]"
        else:
            change_str = "N/A"
            
        if isinstance(market_cap, (int, float)):
            if market_cap >= 1_000_000_000:
                market_cap_str = f"{currency} {market_cap / 1_000_000_000:.2f}B"
            else:
                market_cap_str = f"{currency} {market_cap / 1_000_000:.2f}M"
        else:
            market_cap_str = "N/A"

        if isinstance(volume, (int, float)):
            if volume >= 1_000_000:
                volume_str = f"{volume / 1_000_000:.2f}M"
            else:
                 volume_str = f"{volume / 1_000:.2f}K"
        else:
            volume_str = "N/A"
        
        pe_str = f"{trailing_pe:.2f}" if isinstance(trailing_pe, (int, float)) else "N/A"
        pb_str = f"{price_to_book:.2f}" if isinstance(price_to_book, (int, float)) else "N/A"

        table.add_row(
            symbol,
            name,
            price_str,
            change_str,
            market_cap_str,
            pe_str,
            pb_str,
            volume_str
        )

    main_panel = Panel(
        table,
        title="[bold magenta]Equity Screener Results[/bold magenta]",
        border_style="magenta",
        padding=(1, 1),
        subtitle=f"[dim]Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]"
    )

    console.print(main_panel)





def screen_stocks(state: Annotated[dict, InjectedState],
    screener_type: Literal['equity', 'fund', "predefined"],
    comparison_type: Literal['and', 'or'] | None = None,
    custom_filters: List[Dict[str, Any]] | None = None,
    predefined_screeners: List[str] | None = None,
    sort_field: str = 'percentchange',
    sort_ascending: bool = False,
    count: int = 10):
    """To screen/search for stocks based on the filters present in user prompt

    Args:
        screener_type: choose between equity, fund or predefined screener types
        comparison_type: choose between and/or comparison type between filters
        custom_filters: a dictionary containing the filter_name, operator and value
        predefined_screeners: list of predefined screeners to use
        sort_field: the key to sort the value according to
        sort_ascending: indicates the order of sorting. 'True' for ascending order
        count: the number of stocks to display for each screener. Extract from user prompt if specified.
    """

    console = Console()
    s = Screener()
    c = CurrencyConverter()

    try:
        if predefined_screeners:
            response = s.get_screeners(predefined_screeners, count)

            for screener, screener_dict in response.items():
                display_predefined_screener_results(screener, response[screener].get("quotes", []))
        else:
            if screener_type == "equity":
                for filter in custom_filters:
                    if filter["field"] == 'region' and not isinstance(filter["value"], list):
                        country_currency = country_to_currency.get(filter["value"], "USD")
                    else:
                        country_currency = "USD"

                equity_query_list = []
                for filter in custom_filters:
                    field = filter["field"]
                    operator = filter["operator"]
                    values = filter["value"]

                    if field in screener_fields_needing_conversion:
                        if isinstance(values, list):
                            for i in range(len(values)):
                                values[i] = c.convert(values[i], "USD", country_currency)
                        else:
                            values = c.convert(values, "USD", country_currency)

                    if isinstance(values, list):
                        operand_values = values
                    else:
                        operand_values = [values]
                    
                    equity_query_list.append(EquityQuery(operator = operator, operand = [field] + operand_values))
                
                q = EquityQuery(operator=comparison_type, operand = equity_query_list)
                
                response = yf.screen(q, sortField = sort_field, sortAsc = sort_ascending, size=count)

                display_equity_screener_results(response.get("quotes", []))

            elif screener_type == "fund":
                for filter in custom_filters:
                    if filter["field"] == 'region' and not isinstance(filter["value"], list):
                        country_currency = country_to_currency.get(filter["value"], "USD")
                    else:
                        country_currency = "USD"

                fund_query_list = []
                for filter in custom_filters:
                    field = filter["field"]
                    operator = filter["operator"]
                    values = filter["value"]

                    if field in screener_fields_needing_conversion:
                        if isinstance(values, list):
                            for i in range(len(values)):
                                values[i] = c.convert(values[i], "USD", country_currency)
                        else:
                            values = c.convert(values, "USD", country_currency)

                    if isinstance(values, list):
                        operand_values = values
                    else:
                        operand_values = [values]

                    fund_query_list.append(FundQuery(operator = operator, operand = [field] + operand_values))
                            
                q = FundQuery(operator=operator, operand = fund_query_list)

                response = yf.screen(q, sortField = sort_field, sortAsc = sort_ascending, size=count)
                display_fund_screener_results(response.get("quotes", []))

    except Exception as e:
            prompt = state["messages"][-1]
            display_result_for_unknown_prompts(prompt)
            return "Error: An error occurred while processing your query. Reverting to Any Prompt"