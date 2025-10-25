from langchain_google_genai import ChatGoogleGenerativeAI
from google.ai.generativelanguage_v1beta.types import Tool as GenAITool
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

def display_response(llm_response: str):
    """
    Takes a company name and a free-form text response from an LLM,
    parses it, and displays it in a beautifully structured UI using rich.

    Args:
        company_name: The name of the company (e.g., 'Reliance Industries').
        llm_response: The unstructured string containing the financial summary.
    """
    console = Console()
    
    main_panel = Panel(
        renderable=Markdown(llm_response),
        border_style="magenta",
        padding=(1, 2)
    )
    
    console.print(main_panel)


def display_result_for_unknown_prompts(prompt: str) -> str:
    """
    Displays results for prompts which are not understandable by the llm and cannot be resolved using already available tools.
    
    Args
        prompt: String representing the prompt given by the user.
    """

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", transport="rest")
    message = f"""You are a helpful assistant. A user has asked a question that is outside your primary financial functions. Please provide a helpful, general response to the following query:
    '{prompt}'
    """
    response = llm.invoke(message, tools=[GenAITool(google_search={})])

    display_response(response.content)

    return response.content