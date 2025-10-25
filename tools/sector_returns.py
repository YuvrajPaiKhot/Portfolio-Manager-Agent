from tools.historical_pricing import get_historical_pricing
from mappings import sector_mapping

def general_sector_returns():
    """Returns a dictionary containing periodwise return for all sectors"""
    periods = ["ytd", "1mo", "3mo", "1y", "3y", "5y", "10y"]
    sector_tickers = list(sector_mapping.keys())
    sector_list = list(sector_mapping.values())
    sector_returns = {sector: {} for sector in sector_mapping.values()}

    for period in periods:
        sector_df = get_historical_pricing(sector_tickers, period=period, interval="1d")

        for symbol, symbol_df in sector_df.groupby('symbol'):
            ret = round(((symbol_df.iloc[-1]["close"] - symbol_df.iloc[0]["close"])/symbol_df.iloc[0]["close"]) * 100, 2)
            sector_name = sector_mapping[symbol]
            sector_returns[sector_name][period] = ret

    return {
        "sector_list": sector_list,
        "performance_data": sector_returns
    }



def specific_sector_returns(sectors):
    """Returns a dictionary containing periodwise return for specific sectors"""
    periods = ["ytd", "1mo", "3mo", "1y", "3y", "5y", "10y"]

    sector_returns = {}
    sector_tickers = []
    for ticker, sector in sector_mapping.items():
        if(sector in sectors):
            sector_returns[sector] = {}
            sector_tickers.append(ticker)

    for period in periods:
        sector_df = get_historical_pricing(sector_tickers, period=period, interval="1d")

        for symbol, symbol_df in sector_df.groupby('symbol'):
            ret = round(((symbol_df.iloc[-1]["close"] - symbol_df.iloc[0]["close"])/symbol_df.iloc[0]["close"]) * 100, 2)
            sector_name = sector_mapping[symbol]
            sector_returns[sector_name][period] = ret

    return sector_returns