from functions.holding_functions import HoldingsManager
from currency_converter import CurrencyConverter

def get_sectors_in_portfolio():
    manager = HoldingsManager()
    holdings = manager.list_holdings()

    portfolio_sectors = []

    for holding in holdings:
        sector = holding["sector"]    
        if sector not in portfolio_sectors:
            portfolio_sectors.append(sector)

    return portfolio_sectors



def get_industries_in_portfolio():
    manager = HoldingsManager()
    holdings = manager.list_holdings()

    industries_in_portfolio = {}

    for holding in holdings:
        user_sector = holding["sector"]
        user_industry = holding["industry"]
        if user_sector not in industries_in_portfolio:
            industries_in_portfolio[user_sector] = []
        industries_in_portfolio[user_sector].append(user_industry)

    return industries_in_portfolio

from functions.holding_functions import HoldingsManager
from collections import defaultdict



def get_portfolio_breakdown():
    """
    Analyzes portfolio holdings to calculate the value-weighted percentage contribution
    of each sector to the total portfolio, and each industry within its sector.

    Returns:
        dict: A dictionary containing the total portfolio value, a breakdown of
              sector weights, and a breakdown of industry weights within each sector.
              Returns an empty structure if there are no holdings.
    """
    manager = HoldingsManager()
    holdings = manager.list_holdings()
    c = CurrencyConverter()

    if not holdings:
        return {
            "total_portfolio_value": 0,
            "sector_weights": {},
            "industry_weights": {}
        }

    sector_values = defaultdict(float)
    industry_values = defaultdict(lambda: defaultdict(float))
    total_portfolio_value = 0.0

    for holding in holdings:
        currency = holding.get("currency", "USD")
        price = c.convert(holding.get("price", 0) or 0, currency, "USD")
        quantity = holding.get("quantity", 0) or 0
        
        holding_value = price * quantity
        sector = holding.get("sector", "unknown")
        industry = holding.get("industry", "unknown")

        total_portfolio_value += holding_value
        sector_values[sector] += holding_value
        industry_values[sector][industry] += holding_value

    if total_portfolio_value == 0:
        return {
            "total_portfolio_value": 0,
            "sector_weights": {sector: 0.0 for sector in sector_values},
            "industry_weights": {
                sector: [{"industry": industry, "weight": 0.0} for industry in industries]
                for sector, industries in industry_values.items()
            }
        }

    sector_weights = {
        sector: round((value / total_portfolio_value) * 100, 2)
        for sector, value in sector_values.items()
    }

    industry_weights = {}
    for sector, industries in industry_values.items():
        sector_total_value = sector_values[sector]
        if sector_total_value > 0:
            industry_weights[sector] = [
                {
                    "industry": industry,
                    "weight": round((value / sector_total_value) * 100, 2)
                }
                for industry, value in industries.items()
            ]
        else:
             industry_weights[sector] = [
                {"industry": industry, "weight": 0.0} for industry in industries
            ]


    return {
        "total_portfolio_value": round(total_portfolio_value, 2),
        "sector_weights": sector_weights,
        "industry_weights": industry_weights
    }