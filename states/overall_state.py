from langgraph.graph import MessagesState
from typing import Any

class OverallState(MessagesState):
    user_intent: dict
    tickers: dict
    # risk_assessment: dict
    # market_analysis: dict
    user_profile: dict
    user_sub_intent: dict
    # suggested_sector: dict
    # suggested_industry: dict
    suggestions: dict
    pending_tool_calls: list
    # display: Any
    error: bool
    # balance_sheet: dict
    # valuation_measures: dict
    # income_statement: dict
    # cashflow_statement: dict
    # financial_data: dict
    # summary_detail: dict
    # additional_info: dict
    fund_data: dict
    equity_data: dict
    # analysis: list
