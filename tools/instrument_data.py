from tools.historical_pricing import get_historical_pricing
from tools.financials import get_financial_data
from numpy import nan
import pandas as pd

def get_specific_instrument_returns(instrument):
    periods = ["ytd", "1mo", "3mo", "1y", "3y", "5y"]

    instrument_returns = {}

    for period in periods:
        instrument_df = get_historical_pricing([instrument], period, "1d")

        for symbol, symbol_df in instrument_df.groupby("symbol"):
            ret = round(((symbol_df.iloc[-1]["close"] - symbol_df.iloc[0]["close"])/symbol_df.iloc[0]["close"]) * 100, 2)
            instrument_returns[period] = ret

    return instrument_returns


def get_specific_instrument_sentiment(summary_detail, ticker):
    fifty_day_average = summary_detail.get("fiftyDayAverage", nan)
    two_hundred_day_average = summary_detail.get("twoHundredDayAverage", nan)
    beta = summary_detail.get("beta", nan)
    current_price = summary_detail.get("previousClose", nan)

    historical_pricing = get_historical_pricing([ticker], "60d", "1d")
    rsi = get_specific_instrument_rsi(list(historical_pricing["close"]))

    price_vs_50_day_avg = ((current_price - fifty_day_average)/fifty_day_average) * 100
    price_vs_200_day_avg = ((current_price - two_hundred_day_average)/two_hundred_day_average) * 100

    return {
        "rsi_14_day": rsi,
        "price_vs_50_day_avg": f"{round(price_vs_50_day_avg, 2)}%",
        "price_vs_200_day_avg": f"{round(price_vs_200_day_avg, 2)}%",
        "beta": beta
    }
    

def get_specific_instrument_rsi(prices, period=14):
    if len(prices) < period:
        return None

    price_series = pd.Series(prices)

    delta = price_series.diff(1)
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    
    ema_up = up.ewm(com=period - 1, adjust=False).mean()
    ema_down = down.ewm(com=period - 1, adjust=False).mean()
    
    rs = ema_up / ema_down
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi.iloc[-1], 2)

