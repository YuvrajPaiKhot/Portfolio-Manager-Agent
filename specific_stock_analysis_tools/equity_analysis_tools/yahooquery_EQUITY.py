from rich.console import Console
from tools.financials import get_balance_sheet, get_cashflow_statement, get_financial_data, get_income_statement, get_additional_info, get_valuation_measures, get_summary_profile, get_summary_detail

def stringify_keys(obj):
    if isinstance(obj, dict):
        return {str(k): stringify_keys(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [stringify_keys(i) for i in obj]
    else:
        return obj


def gather_yfinance_equity_data(tickers):

    console = Console()
    console.print("Gathering data from yahooquery...", style="dim italic")
    # tickers = state.get("tickers", {})

    valuation_measures = {}
    income_statement = {}
    cash_flow = {}
    balance_sheet = {}
    financial_data = {}
    additional_info = {}


    for company in tickers:
        try:
            ticker = tickers[company]

            valuation_measures[ticker] = get_valuation_measures(ticker)

            income_statement[ticker] = get_income_statement(ticker, 'q', True)

            cash_flow[ticker] = get_cashflow_statement(ticker, 'q', True)

            balance_sheet[ticker] = get_balance_sheet(ticker, 'q')

            exchange, quoteType, longName, shortName = get_additional_info(ticker)

            sectorKey, industryKey = get_summary_profile(ticker)

            additional_info_dict = {
                "longName": longName,
                "shortName": shortName,
                "sectorKey": sectorKey,
                "industryKey": industryKey,
                "exchange": exchange,
                "quoteType": quoteType,
                "summary_detail": get_summary_detail(ticker)
            }
            
            additional_info[ticker] = dict(additional_info_dict)

            financial_data[ticker] = get_financial_data(ticker)
            
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            continue

    equity_data = {
            "valuation_measures": valuation_measures,
            "income_statement": income_statement,
            "balance_sheet": balance_sheet,
            "cashflow_statement": cash_flow,
            "financial_data": financial_data,
            "additional_info": additional_info
        }

    return equity_data

    