import pandas as pd
from yahooquery import Ticker
from langchain_google_genai import ChatGoogleGenerativeAI
from google.ai.generativelanguage_v1beta.types import Tool as GenAITool

def get_valuation_measures(ticker):
    stock = Ticker(ticker)
    valuation_measures_df = stock.valuation_measures

    if(not isinstance(valuation_measures_df, str)):
        return valuation_measures_df
    else:
        return pd.DataFrame() 

    


def get_income_statement(ticker, frequency, trailing):
    stock = Ticker(ticker)
    income_statement_df = stock.income_statement(frequency=frequency, trailing=trailing)
    income_statement_df_annual = stock.income_statement(frequency='a', trailing=False)

    if(not isinstance(income_statement_df, str) and not isinstance(income_statement_df_annual, str)):
        final_df = pd.concat([income_statement_df, income_statement_df_annual])
    else:
        return pd.DataFrame()

    return final_df


def get_cashflow_statement(ticker, frequency, trailing):
    stock = Ticker(ticker)

    cashflow_statement_df = stock.cash_flow(frequency=frequency, trailing=trailing)
    cashflow_statement_df_annual = stock.cash_flow(frequency='a', trailing=False)

    if(not isinstance(cashflow_statement_df, str) and not isinstance(cashflow_statement_df_annual, str)):
        final_df = pd.concat([cashflow_statement_df, cashflow_statement_df_annual])
    else:
        return pd.DataFrame()

    return final_df


def get_balance_sheet(ticker, frequency):
    stock = Ticker(ticker)

    balance_sheet_df = stock.balance_sheet(frequency=frequency)
    balance_sheet_df_annual = stock.balance_sheet(frequency='a')

    if(not isinstance(balance_sheet_df, str) and not isinstance(balance_sheet_df_annual, str)):
        final_df = pd.concat([balance_sheet_df, balance_sheet_df_annual]).drop_duplicates()
    else:
        return pd.DataFrame()

    return final_df


def get_additional_info(ticker):
    stock = Ticker(ticker)

    company_dict = stock.quote_type[ticker]
    exchange = company_dict.get("exchange", None)
    quote_type = company_dict.get("quoteType", None)
    long_name = company_dict.get("longName", None)
    short_name = company_dict.get("shortName", None)

    return exchange, quote_type, long_name, short_name

def get_summary_profile(ticker):
    stock = Ticker(ticker)

    company_dict = stock.summary_profile[ticker]

    sector_key = company_dict.get("sectorKey", None)
    industry_key = company_dict.get("industryKey", None)

    return sector_key, industry_key


def get_summary_detail(ticker):
    stock = Ticker(ticker)

    company_dict = stock.summary_detail[ticker]

    return company_dict


def get_financial_data(ticker):
    stock = Ticker(ticker)

    financials = stock.financial_data[ticker]

    return financials


def get_fund_performance(ticker):
    stock = Ticker(ticker)

    fund_performance = stock.fund_performance[ticker]

    return fund_performance


def get_fund_sector_weightings(ticker):
    stock = Ticker(ticker)

    fund_sector_weightings = stock.fund_sector_weightings

    fund_sector_weightings = fund_sector_weightings[fund_sector_weightings[ticker] != 0].to_dict()[ticker]

    return fund_sector_weightings


def get_fund_valuation_measures(ticker):
    stock = Ticker(ticker)

    fund_valuation_measures = stock.fund_equity_holdings[ticker]

    return fund_valuation_measures

def get_financial_news(company, ticker):
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    response = llm.invoke(
        f"Give me all the recent financial news for {company} - {ticker}",
        tools=[GenAITool(google_search={})],
    )

    return response.content