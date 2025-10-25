from langchain_google_genai import ChatGoogleGenerativeAI
from google.ai.generativelanguage_v1beta.types import Tool as GenAITool
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

def display_financial_summary(company_name: str, llm_response: str):
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
        title=f"[bold magenta]Latest News: {company_name}[/bold magenta]",
        border_style="magenta",
        padding=(1, 2)
    )
    
    console.print(main_panel)

def get_financial_news(companies: list[str] | None = None) -> str:
    """
    Fetches recent financial news for a list of companies.

    Args:
        companies: A list of companies to get news for.
    """
    console = Console()
    if not companies:
        console.print("[bold red]Error: Please specifiy company to fetch news for![/bold red]")
        return "Error: Please specifiy company to fetch news for!"
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", transport="rest")
    for company in companies:
        response = llm.invoke(f"Give me all the recent financial news for {company}.", tools=[GenAITool(google_search={})])
        display_financial_summary(company, response.content)


