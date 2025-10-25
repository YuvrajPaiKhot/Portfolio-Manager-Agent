from rich.console import Console
from tools.financials import get_additional_info, get_summary_detail, get_fund_performance, get_fund_sector_weightings, get_fund_valuation_measures

def stringify_keys(obj):
    if isinstance(obj, dict):
        return {str(k): stringify_keys(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [stringify_keys(i) for i in obj]
    else:
        return obj


def gather_yahooquery_mf_data(tickers):

    console = Console()
    console.print("Gathering data from yahooquery...", style="dim italic")

    additional_info = {}
    fund_sector_weightings = {}
    fund_performance = {}
    fund_data = {}


    for company in tickers:
        try:
            ticker = tickers[company]

            fund_sector_weightings = get_fund_sector_weightings(ticker)
            fund_performance = get_fund_performance(ticker)
            fund_valuation_measures = get_fund_valuation_measures(ticker)

            exchange, quoteType, longName, shortName = get_additional_info(ticker)

            additional_info_dict = {
                "longName": longName,
                "shortName": shortName,
                "exchange": exchange,
                "quoteType": quoteType,
                "summary_detail": get_summary_detail(ticker)
            }
            
            additional_info = dict(additional_info_dict)

            fund_data[ticker] = {
                "fund_performance": fund_performance,
                "fund_sector_weightings": fund_sector_weightings,
                "fund_valuation_measures": fund_valuation_measures,
                "additional_info": additional_info
            }
            
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            continue

    return fund_data

    