from yahooquery import Ticker

def get_historical_pricing(ticker_list, period, interval="1d"):
    tickers = Ticker(ticker_list, asynchronous=True)

    history = tickers.history(period=period, interval=interval)

    return history