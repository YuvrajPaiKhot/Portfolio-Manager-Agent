from tools.portfolio_stats import get_portfolio_breakdown
from tools.sector_returns import general_sector_returns
from tools.industry_returns import general_industry_returns, get_industry_top_companies
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
import json

from rich.panel import Panel
from rich.console import Console, Group
from rich.text import Text
from rich.table import Table
from rich.padding import Padding
import pandas as pd
from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated

response_schema = {
    "type": "object",
    "properties": {
        "portfolio_analysis": {
            "type": "string",
            "description": "Analysis of the user's portfolio."
        },
        "recommendations": {
            "type": "array",
            "description": "A list of recommended sectors, each containing the specific, high-potential industries that align with the user's portfolio goals and risk profile.",
            "items": {
                "type": "object",
                "properties": {
                    "sector": {
                        "type": "string",
                        "description": "The name of the recommended parent sector (e.g., 'healthcare'). This serves as the primary grouping for the investment idea.",
                        "enum": ["basic-materials", "communication-services", "consumer-cyclical", "consumer-defensive", "energy", "financial-services", "healthcare", "industrials", "real-estate", "technology", "utilities"],

                    },
                    "analysis": {
                        "type": "string",
                        "description": "A detailed justification explaining WHY this sector and its selected industries are a strategic fit. It must reference the user's current portfolio concentration, their risk profile, and cite specific performance data to support the recommendation."
                    },
                    "selected_industries": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "A list of one or more specific industries within the recommended sector to invest in. This is the core, actionable advice."
                    }
                },
                "required": ["sector", "analysis", "selected_industries"]
            }
        }
    }
}


def display_recommendations(llm_output: dict, industry_data: dict):
    """
    Takes the full LLM output and top companies data, and displays them
    in a structured and visually appealing UI using the rich library.
    """
    console = Console()

    portfolio_analysis = llm_output.get("portfolio_analysis", "No portfolio analysis was provided.")
    recommendations = llm_output.get("recommendations", [])

    summary_panel = Panel(
        Text(portfolio_analysis, justify="left", style="dim"),
        title="[bold magenta]Overall Portfolio Strategy[/bold magenta]",
        border_style="magenta",
        padding=(1, 2)
    )
    console.print(summary_panel)

    for item in recommendations:
        sector_raw = item.get("sector", "N/A")
        sector_title = sector_raw.replace("-", " ").title()
        analysis = item.get("analysis", "No analysis provided.")
        selected_industries = item.get("selected_industries", [])

        sector_content_group = []

        sector_content_group.append(Padding(Text(analysis, style="italic"), (0, 1, 1, 1)))

        for industry_raw in selected_industries:
            industry_title = industry_raw.replace("-", " ").title()
            
            industry_tables = []
            
            def _create_company_table(title: str, df: pd.DataFrame, emoji: str):
                if df is None or df.empty:
                    return Text(f"{emoji} {title}: No data available.", style="dim")
                
                table = Table(title=f"{emoji} {title}", title_style="bold", border_style="dim", show_header=True, header_style="bold cyan")
                
                for column in df.columns:
                    table.add_column(str(column).title())
                
                for _, row in df.iterrows():
                    table.add_row(*[f"{val:.2f}" if isinstance(val, float) else str(val) for val in row])
                return table

            company_data = industry_data.get(sector_raw, {}).get(industry_raw, {})
            
            industry_tables.append(_create_company_table("Top Companies by Weight", company_data.get("top_companies"), "🏆"))
            industry_tables.append(_create_company_table("Top Performers (YTD)", company_data.get("top_performing_companies"), "🚀"))
            industry_tables.append(_create_company_table("Top Growth Companies", company_data.get("top_growth_companies"), "📈"))

            industry_panel = Panel(
                Group(*industry_tables),
                title=f"[bold]Industry: {industry_title}[/bold]",
                border_style="green",
                padding=(1, 1)
            )
            sector_content_group.append(industry_panel)

        sector_panel = Panel(
            Group(*sector_content_group),
            title=f"[bold cyan]Recommendation: {sector_title}[/bold cyan]",
            border_style="cyan",
            padding=(1, 1)
        )
        console.print(sector_panel)


def get_metric_data_package(user_profile, user_portfolio, sector_returns, industry_returns, user_preferred_sectors, user_excluded_sectors):

    data_package = {
        "user_profile": user_profile,
        "user_portfolio": user_portfolio,
        "user_preferred_sectors": user_preferred_sectors,
        "user_excluded_sectors": user_excluded_sectors,
        "available_sectors": sector_returns,
        "available_industries": industry_returns
    }
    
    return data_package
    

def get_sector_industry_recommendation(state: Annotated[dict, InjectedState], included_sectors: list[str] | None = None, excluded_sectors: list[str] | None = None) -> str:
    """
    Generates recommendations from strategic sectors for the user to invest in.

    Args
        included_sectors: List of string containing sectors the user wants to analyze.
        excluded_sectors: List of string containing the sectors the user doesn't want recommendations from.
    """
    if included_sectors is None:
        included_sectors = []
    if excluded_sectors is None:
        excluded_sectors = []

    console = Console()
    console.print("Generating recommendations...", style="dim italic")
    user_profile = state.get("user_profile", {})
    user_portfolio = get_portfolio_breakdown()
    sector_data = general_sector_returns()
    industry_data = general_industry_returns()

    data_package = get_metric_data_package(user_profile, user_portfolio, sector_data, industry_data, included_sectors, excluded_sectors)

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.4, top_p=0.85, top_k=40, response_schema=response_schema, response_mime_type="application/json", transport="rest")

    sys_message = SystemMessage(content="""{
        "role": "system",
        "purpose": "To act as an Integrated Portfolio Strategist. Your goal is to analyze a user's current portfolio and market data to provide personalized sector and industry recommendations that align with the user's profile and explicit preferences.",
        "input_expectation": "A single JSON object is provided. It contains: (A) a 'user_profile', (B) the 'user_portfolio' with value-weighted percentages, (C) 'user_preferred_sectors' (optional), (D) 'user_excluded_sectors' (optional), and (E) performance data for all available sectors and industries.",
        "decision_framework": {
            "core_strategy": "Your primary function is to act on the user's instructions while providing expert, data-driven analysis. First, generate a standalone analysis of the user's current portfolio. Second, generate specific investment recommendations based on a strict filtering process that respects all user preferences.",
            "priority_order": [
                "1. Generate Portfolio Analysis: Create a concise, data-driven summary of the user's current portfolio, highlighting the largest sector concentrations and the overall risk profile based on sector categories.",
                "2. Apply User Filters (Strict):",
                    " - If 'user_preferred_sectors' is provided, your search for recommendations is LIMITED ONLY to these sectors.",
                    " - From the remaining available sectors, you MUST REMOVE any sectors listed in 'user_excluded_sectors'.",
                    " - If no preferred sectors are given, start with all available sectors and then apply exclusions.",
                "3. Identify Top Industries: Within the filtered list of sectors, identify the best-performing industries that align with the user's 'risk_tolerance' and 'investment_horizon'.",
                "4. Group and Finalize: Group the recommended industries by their parent sector. For each sector, provide a brief analysis.",
                "5. Add Cautious Warnings: Even when following a user's preference, you must act responsibly. If a user's choice (e.g., selecting a sector they are already concentrated in) increases portfolio risk, you MUST mention this clearly in that sector's 'analysis' text."
            ],
            "personalization_logic": {
                "risk_tolerance_guidance": {
                    "description": "Use the user's risk tolerance to guide industry selection within the filtered sectors.",
                    "sector_categories": {
                        "growth_volatile": ["technology", "consumer-cyclical", "communication-services", "energy"],
                        "defensive_stable": ["utilities", "consumer-defensive", "healthcare", "real-estate"],
                        "balanced": ["industrials", "financial-services", "basic-materials"]
                    },
                    "rules": {
                        "aggressive": "Focus on the highest-performing industries, primarily from the 'growth_volatile' sectors.",
                        "moderate": "Seek industries with strong, consistent performance from 'balanced' or 'defensive_stable' sectors.",
                        "conservative": "Strongly prefer stable, positive-performing industries from the 'defensive_stable' sectors."
                    }
                },
                "investment_horizon_guidance": {
                    "description": "Use the user's investment horizon to prioritize performance metrics.",
                    "rules": {
                        "long-term": "Prioritize industry performance over the 'oneYear', 'threeYear', and 'fiveYear' horizons.",
                        "short-term": "Prioritize industry performance over the 'ytd', 'oneMonth', and 'threeMonth' horizons."
                    }
                }
            }
        },
        "formatting_rules": {
            "output_only": "Return a single valid JSON object. No extra text outside the JSON.",
            "numeric_reference": "In your analysis, cite specific performance data and portfolio weights to justify your choices."
        },
        "example": {
            "input": {
                "user_profile": { "risk_tolerance": "moderate", "investment_horizon": "long-term" },
                "user_portfolio": {
                    "sector_weights": { "technology": 76.7, "financial-services": 23.3 }
                },
                "user_preferred_sectors": ["technology", "healthcare"],
                "user_excluded_sectors": ["energy"],
                "available_industries": {
                    "technology": {
                        "performance_data": { "cybersecurity": { "fiveYear": 120.5 } }
                    },
                    "healthcare": {
                        "performance_data": { "medical-devices": { "fiveYear": 75.1 } }
                    }
                }
            },
            "output": {
                "portfolio_analysis": "Your current portfolio has a heavy 76.7% concentration in the Technology sector, which is a significant risk for a 'moderate' investor. This allocation is heavily skewed towards growth, leaving it vulnerable to market rotations. The following recommendations are based on your specific requests.",
                "recommendations": [
                    {
                        "sector": "technology",
                        "analysis": "You expressed interest in the Technology sector. While adding more to this area will increase your already high concentration risk, 'cybersecurity' is a strong performer with a fiveYear return of +120.5%. This could be a way to add a different growth driver within your existing allocation.",
                        "selected_industries": ["cybersecurity"]
                    },
                    {
                        "sector": "healthcare",
                        "analysis": "As requested, the Healthcare sector is an excellent choice for diversification. 'medical-devices' aligns well with your long-term, moderate-risk profile, showing stable and positive returns (fiveYear: +75.1%) and adding a defensive component to your portfolio.",
                        "selected_industries": ["medical-devices"]
                    }
                ]
            }
        }
    }
    """)

    human_msg = HumanMessage(content=f"""Please analyze the input provided according to the guidelines given in the system prompt
        ```
        {json.dumps(data_package, indent=2)}
        ```
    """)

    response = llm.invoke([sys_message] + [human_msg])

    output = json.loads(response.content)

    industry_top_companies = get_industry_top_companies(output.get("recommendations", []))

    display_recommendations(output, industry_top_companies)

    return "Recommendations generated successfully"


