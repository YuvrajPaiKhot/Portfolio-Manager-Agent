from langgraph.graph import END

def route_to_next_tool(state):
    tool_calls = state["pending_tool_calls"]

    if(len(tool_calls) > 0):
        return "tool_executor"
    else:
        return END