from portfolio_analysis_tools.report_generator import generate_portfolio_report

from portfolio_management_tools.database_add import add_to_database
from portfolio_management_tools.database_update import update_database
from portfolio_management_tools.database_list import list_database
from portfolio_management_tools.database_clear import clear_database
from portfolio_management_tools.database_get_by_trans_id import get_by_trans
from portfolio_management_tools.database_get_name import get_database_by_name
from portfolio_management_tools.database_delete_name import delete_database_by_name
from portfolio_management_tools.database_delete_trans_id import delete_database_by_trans

from portfolio_recommendation_tools.super_portfolio_recommendation import get_sector_industry_recommendation

from specific_stock_analysis_tools.super_stock_analyzer import specific_stock_analysis

from screener_tools.stock_screener import screen_stocks

from tools.display_financial_news import get_financial_news
from tools.any_prompt import display_result_for_unknown_prompts

from langchain_core.messages import ToolMessage

def execute_tools(state):
    tool_call = state['pending_tool_calls'].pop(0)
    tool_name = tool_call['name']
    tool_args = tool_call['args']

    if tool_name == "add_to_database":
        result = add_to_database(tool_args.get("company", None), tool_args.get("quantity", None), tool_args.get("price", None))
    elif tool_name == "update_database":
        result = update_database(tool_args.get("transaction_id", ""), tool_args.get("new_quantity", -1), tool_args.get("new_price", -1))
    elif tool_name == "list_database":
        result = list_database()
    elif tool_name == "clear_database":
        result = clear_database()
    elif tool_name == "get_by_trans":
        result = get_by_trans(tool_args.get("transaction_id", ""))
    elif tool_name == "get_database_by_name":
        result = get_database_by_name(tool_args.get("companies", []))
    elif tool_name == "delete_database_by_name":
        result =  delete_database_by_name(tool_args.get("companies", []))
    elif tool_name == "delete_database_by_trans":
        result = delete_database_by_trans(tool_args.get("transaction_id", ""))
    elif tool_name == "generate_portfolio_report":
        result = generate_portfolio_report()
    elif tool_name == "get_sector_industry_recommendation":
        result = get_sector_industry_recommendation(state=state, included_sectors=tool_args.get("included_sectors", None), excluded_sectors=tool_args.get("excluded_sectors", None))
    elif tool_name == "specific_stock_analysis":
        result = specific_stock_analysis(tool_args.get("companies", []), state)
    elif tool_name == "screen_stocks":
        result = screen_stocks(state, tool_args.get("screener_type", None), tool_args.get("comparison_type", "and"), tool_args.get("custom_filters", []), tool_args.get("predefined_screeners", []), tool_args.get("sort_field", "percentchange"), tool_args.get("sort_ascending", False), tool_args.get("count", 10))
    elif tool_name == "display_result_for_unknown_prompts":
        result = display_result_for_unknown_prompts(tool_args.get("prompt", ""))
    elif tool_name == "get_financial_news":
        result = get_financial_news(tool_args.get("companies", []))
    else:
        result = f"Error: {tool_name} not found!"

    tool_message = ToolMessage(content=result, tool_call_id=tool_call['id'])

    return {"messages": [tool_message], "pending_tool_calls": state['pending_tool_calls']}