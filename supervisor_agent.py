from agents.process_input import parse_user_input

from nodes.next_tool_router import route_to_next_tool
from nodes.tool_executor_node import execute_tools

from states.overall_state import OverallState
from langgraph.graph import StateGraph, START, END

from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.table import Table
import traceback
import json

overallGraph = StateGraph(OverallState)
overallGraph.add_node("parse_user_input", parse_user_input)
overallGraph.add_node("tool_executor", execute_tools)

overallGraph.add_edge(START, "parse_user_input")
overallGraph.add_edge("parse_user_input", "tool_executor")
overallGraph.add_conditional_edges("tool_executor", route_to_next_tool, ["tool_executor", END])

graph = overallGraph.compile()

console = Console()

if __name__ == "__main__":
    console.print("[bold green]Welcome to the Financial Advisor Bot![/bold green]")
    console.print("Type 'quit' or 'exit' to end the session.\n")

    file_path = "C:\\Users\\yuvra\\OneDrive\\Desktop\\Portfolio Manager Agent\\Database\\settings.json"

    settings = {}
    with open(file_path, "r") as  f:
        settings = json.load(f)

    if(settings["user_profile_created"] == False):
        console.print("[bold yellow]You haven't created a profile yet. Please create one to continue.[/bold yellow]\n")
        name = Prompt.ask("Enter your name")
        age = Prompt.ask("Enter your age")
        risk_tolerance = Prompt.ask("What is your risk tolerance?", choices=["low", "moderate", "high"], case_sensitive=False)

        table = Table()
        table.add_column("Choice", justify="center")
        table.add_column("Investment Horizon", justify="center")
        table.add_row("1", "Short-term (1-3 years)")
        table.add_row("2", "Medium-term (3-7 years)")
        table.add_row("3", "Long-term (7+ years)")
        console.print(table)
        choice = IntPrompt.ask("What is your investment horizon?", choices=["1","2","3"])

        investment_horizon = "Long-term (7+ years)"
        if(choice == 1):
            investment_horizon = "Short-term (1-3 years)"
        elif(choice == 2):
            investment_horizon = "Medium-term (3-7 years)"
        else:
            investment_horizon = "Long-term (7+ years)"

        user_profile = {
            "name": name,
            "age": age,
            "risk_tolerance": risk_tolerance,
            "investment_horizon": investment_horizon
        }

        settings["user_profile"] = user_profile
        settings["user_profile_created"] = True

        with open(file_path, "w") as f:
            json.dump(settings, f, indent=4)

    else:
        user_profile = settings["user_profile"]
    
    while True:
        try:
            prompt = input("\n🤖 Your prompt: ")
            if prompt.lower() in ["quit", "exit"]:
                console.print("[bold red]Goodbye![/bold red]")
                break
            
            result = graph.invoke(
                {"messages": [{"role": "user", "content": prompt}], "user_profile": user_profile},
                config={"configurable": {"thread_id": 1}}
            )

        except KeyboardInterrupt:
            console.print("[bold red]Goodbye![/bold red]")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            traceback.print_exc()


