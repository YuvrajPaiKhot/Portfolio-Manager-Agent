from langgraph.graph import MessagesState
from typing import Any

class OverallState(MessagesState):
    user_intent: dict
    tickers: dict
    user_profile: dict
    user_sub_intent: dict
    suggestions: dict
    pending_tool_calls: list
    error: bool
    fund_data: dict
    equity_data: dict
