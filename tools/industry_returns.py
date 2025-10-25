from tools.historical_pricing import get_historical_pricing
from mappings import sector_industry_mapping_dict
from tools.instrument_data import get_specific_instrument_returns
import yfinance as yf

def general_industry_returns():
    """
    Returns a dictionary of periodwise returns for all industries
    """
    periods = ["ytd", "1mo", "3mo", "1y", "3y", "5y", "10y"]
    sectors = list(sector_industry_mapping_dict.keys())
    industry_returns = {sector: {} for sector in sectors}

    all_industry_tickers = []
    ticker_to_info_map = {}

    for sector, industries in sector_industry_mapping_dict.items():
        for ticker, industry_name in industries.items():
            all_industry_tickers.append(ticker)
            ticker_to_info_map[ticker] = {"sector": sector, "name": industry_name}

    for period in periods:
        industry_df = get_historical_pricing(all_industry_tickers, period=period, interval="1d")

        for symbol, symbol_df in industry_df.groupby('symbol'):
            if symbol_df.empty:
                continue

            ret = round(((symbol_df.iloc[-1]["close"] - symbol_df.iloc[0]["close"]) / symbol_df.iloc[0]["close"]) * 100, 2)
            
            info = ticker_to_info_map[symbol]
            sector_name = info["sector"]
            industry_name = info["name"]

            if("performance_data" not in industry_returns[sector_name]):
                industry_returns[sector_name]["performance_data"] = {}

            if("industry_list" not in industry_returns[sector_name]):
                industry_returns[sector_name]["industry_list"] = []

            if industry_name not in industry_returns[sector_name]["performance_data"]:
                industry_returns[sector_name]["performance_data"][industry_name] = {}
            
            industry_returns[sector_name]["industry_list"].append(industry_name)
            industry_returns[sector_name]["performance_data"][industry_name][period] = ret

    return industry_returns






def specific_sector_industry_returns(sectors_to_process):
    """
    Returns a dictionary of periodwise returns for all industries 
    from the specified sectors.
    
    Args:
        sectors_to_process (list): A list of sector names to process.
    """
    periods = ["ytd", "1mo", "3mo", "1y", "3y", "5y", "10y"]
    
    industry_returns = {sector: {} for sector in sectors_to_process}

    all_industry_tickers = []
    ticker_to_info_map = {}

    for sector in sectors_to_process:
        if sector in sector_industry_mapping_dict:
            industries = sector_industry_mapping_dict[sector]
            for ticker, industry_name in industries.items():
                all_industry_tickers.append(ticker)
                ticker_to_info_map[ticker] = {"sector": sector, "name": industry_name}
        else:
            print(f"Warning: Sector '{sector}' not found and will be skipped.")

    for period in periods:
        if not all_industry_tickers:
            continue
            
        industry_df = get_historical_pricing(all_industry_tickers, period=period, interval="1d")

        for symbol, symbol_df in industry_df.groupby('symbol'):
            if symbol_df.empty:
                continue

            ret = round(((symbol_df.iloc[-1]["close"] - symbol_df.iloc[0]["close"]) / symbol_df.iloc[0]["close"]) * 100, 2)
            
            info = ticker_to_info_map[symbol]
            sector_name = info["sector"]
            industry_name = info["name"]

            if industry_name not in industry_returns[sector_name]:
                industry_returns[sector_name][industry_name] = {}
            
            industry_returns[sector_name][industry_name][period] = ret


    return industry_returns


def get_industry_top_companies(recommendations):

    industry_top_companies = {}

    for item in recommendations:
        sector = item.get("sector", "N/A")
        analysis = item.get("analysis", "N/A")
        selected_industry_list = item.get("selected_industries", "N/A")

        industry_top_companies[sector] = {}
        industry_top_companies[sector]["analysis"] = analysis

        for industry in selected_industry_list:
            industry_top_companies[sector][industry] = {}

            industry_obj = yf.Industry(industry)
            top_companies = industry_obj.top_companies
            top_performing_companies = industry_obj.top_performing_companies
            top_growth_companies = industry_obj.top_growth_companies

            top_companies["market weight"] = round(top_companies["market weight"] * 100, 2)
            top_companies = top_companies[:5]
            industry_top_companies[sector][industry]["top_companies"] = top_companies

            top_performing_companies["ytd return"] = round(top_performing_companies["ytd return"] * 100, 2)
            top_performing_companies = top_performing_companies[:5]
            industry_top_companies[sector][industry]["top_performing_companies"] = top_performing_companies

            top_growth_companies["ytd return"] = round(top_growth_companies["ytd return"] * 100, 2)
            top_growth_companies[" growth estimate"] = round(top_growth_companies[" growth estimate"] * 100, 2)
            top_growth_companies = top_growth_companies[:5]
            industry_top_companies[sector][industry]["top_growth_companies"] = top_growth_companies

    return industry_top_companies



