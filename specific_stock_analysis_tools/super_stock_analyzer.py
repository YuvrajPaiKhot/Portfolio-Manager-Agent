from tools.ticker import get_tickers
from yahooquery.ticker import Ticker
from rich.console import Console
from typing_extensions import Annotated
from langgraph.prebuilt import InjectedState
from specific_stock_analysis_tools.equity_analysis_tools.super_investment_advisor_EQUITY import investment_advice_equity
from specific_stock_analysis_tools.mf_analysis_tools.super_analysis_MF import analyze_MF

def specific_stock_analysis(companies: list[str], state: Annotated[dict, InjectedState]):
    """
    Analyzes financial instruments like equities and mutual funds

    Args:
        companies: List of string containing companies and tickers extracted from the user prompt
    """

    console = Console()

    equity_dict = {}
    mf_dict = {}

    tickers = get_tickers(companies)

    for company, ticker in tickers.items():

        stock = Ticker(ticker)
        company_dict = stock.quote_type[ticker]

        quote_type = company_dict.get("quoteType", None)

        if quote_type == "EQUITY":
            equity_dict[company] = ticker
        elif quote_type == "MUTUALFUND":
            mf_dict[company] = ticker
        else:
            console.print(f"[bold red]Error: Quote type {quote_type} for company {company} is not supported[/bold red]")

    if equity_dict:
        console.print("Generating Equity investment advice", style="dim italic")
        investment_advice_equity(equity_dict, state)
    
    if mf_dict:
        console.print("Genrating Mutual Fund investment advice...", style="dim italic")
        analyze_MF(mf_dict, state)
