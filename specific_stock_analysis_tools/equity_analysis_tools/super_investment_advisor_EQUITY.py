from langchain_core.messages import HumanMessage, SystemMessage
import json
from langchain_google_genai import ChatGoogleGenerativeAI

from rich.panel import Panel
from rich.console import Console, Group
from rich.text import Text
from rich.table import Table
from numpy import nan
from tools.instrument_data import get_specific_instrument_returns, get_specific_instrument_sentiment
from specific_stock_analysis_tools.equity_analysis_tools.yahooquery_EQUITY import gather_yfinance_equity_data
from specific_stock_analysis_tools.equity_analysis_tools.super_analysis_EQUITY import analyze_EQUITY


response_schema = {
    "type": "object",
    "properties": {
        "company": {
            "type": "string",
            "description": "Name of the company being analyzed."
        },
        "recommendation": {
            "type": "string",
            "description": "The final, clear investment recommendation. Must be one of three values: 'Buy', 'Sell', or 'Hold'."
        },
        "rationale": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "A concise, top-level summary explaining the core logic behind the recommendation. This should synthesize the most critical factors—balancing the fundamental analysis with market sentiment and the user's profile—that led to the final decision."
                },
                "alignment_with_profile": {
                    "type": "string",
                    "description": "A personalized explanation of how the recommendation specifically aligns with the user's provided risk tolerance and investment horizon. It answers the question: 'Why is this the right move for me?'"
                },
                "potential_rewards": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "A bulleted list highlighting the key potential upsides or strengths supporting the recommendation. This should draw from positive data points like strong growth, positive market momentum, or favorable analyst ratings."
                },
                "potential_risks": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "A bulleted list of the most significant risks or weaknesses that temper the recommendation. This should clearly state the potential downsides, such as poor financial health, high valuation, or negative market trends."
                }
            },
            "required": ["summary", "alignment_with_profile", "potential_rewards", "potential_risks"]
        }
    },
    "required": ["company", "recommendation", "rationale"]
}


def display_investment_advice(analyzed_items):
    """
    Takes a list of analyzed items (conforming to the new schema) and 
    formats them into a structured, visually appealing layout in the console.
    """
    console = Console()

    for item in analyzed_items:
        # --- Safely extract data from the new schema ---
        company = item.get("company", "N/A")
        recommendation = item.get("recommendation", "N/A")
        rationale = item.get("rationale", {})
        
        summary = rationale.get("summary", "No summary provided.")
        alignment = rationale.get("alignment_with_profile", "No profile alignment provided.")
        rewards = rationale.get("potential_rewards", [])
        risks = rationale.get("potential_risks", [])

        # --- Style the recommendation ---
        if recommendation.lower() == "buy":
            rec_style = "bold green"
        elif recommendation.lower() == "sell":
            rec_style = "bold red"
        else:
            rec_style = "bold yellow"

        # --- Build the Header Section ---
        header = Text()
        header.append("Recommendation: ", style="bold")
        header.append(f"{recommendation.upper()}\n\n", style=rec_style)
        header.append(f"{summary}\n", style="italic")

        # --- Create a Pros and Cons Table ---
        pros_cons_table = Table.grid(expand=True, padding=(0, 2))
        pros_cons_table.add_column("Rewards", style="green", justify="left")
        pros_cons_table.add_column("Risks", style="red", justify="left")

        rewards_text = Text()
        for reward in rewards:
            rewards_text.append(f"✅ {reward}\n\n")
        
        risks_text = Text()
        for risk in risks:
            risks_text.append(f"❌ {risk}\n\n")

        pros_cons_table.add_row(rewards_text, risks_text)
        
        # --- Assemble all components for the panel ---
        content_group = Group(
            header,
            Panel(Text(alignment, justify="left"), title="[bold]Alignment with Your Profile[/bold]", border_style="dim", padding=(1, 2)),
            Panel(pros_cons_table, title="[bold]Key Considerations[/bold]", border_style="dim", padding=(1, 2))
        )

        # --- Create the final panel for the company ---
        company_panel = Panel(
            content_group,
            title=f"[bold cyan]{company}[/bold cyan]",
            border_style="cyan",
            expand=True,
            padding=(1, 2)
        )
        
        console.print(company_panel)





def get_company_datapackage(user_profile, analysis_data, returns, sentiment, analyst_outlook):

    input_datapackage = {
        "company": analysis_data.get("company", ""),
        "sector": analysis_data.get("sector", ""),
        "user_profile": user_profile,
        "fundamental_analysis": {
            "overall_summary": analysis_data.get("overall_summary", ""),
            "thematic_analysis": analysis_data.get("thematic_analysis", {}),
            "key_flags": analysis_data.get("key_flags", []),
            "market_score": analysis_data.get("market_score", nan),
            "confidence": analysis_data.get("confidence", nan)
        },
        "market_performance": returns,
        "market_sentiment": sentiment,
        "analyst_outlook": analyst_outlook
    }

    return input_datapackage




def investment_advice_equity(tickers: dict[str, str], state):
    """
    To analyze a list of Companies.

    Args
        companies: List of companies you want to analyze
    """

    console = Console()

    # console.print("Generating Investmet Advice...", style="dim italic")
    print("\n")

    # tickers = get_tickers(companies)
    equity_data = gather_yfinance_equity_data(tickers)
    analysis = analyze_EQUITY(equity_data)

    # print(json.dumps(equity_data, indent=2))

    # equity_data = state["equity_data"]

    # analysis = equity_data.get("analysis", [])
    financial_data = equity_data.get("financial_data", {})
    additional_info = equity_data.get("additional_info", {})

    if not analysis:
        return {
            "error": True
        }
    
    company_data_package = {}
    companies = [item["company"] for item in analysis]

    for item in analysis:
        company = item["company"]
        summary_detail = additional_info[company].get("summary_detail", {})

        returns = get_specific_instrument_returns(company)
        anayst_outlook = {
            "consensus_rating": financial_data[company].get("recommendationKey", ""),
            "average_price_target": f"{financial_data[company].get("targetMeanPrice", nan)} {financial_data[company].get("financialCurrency", "USD")}",
            "analyst_count": financial_data[company].get("numberOfAnalystOpinions", nan)
        }
        sentiment = get_specific_instrument_sentiment(summary_detail, company)

        user_profile = state.get("user_profile", {})

        company_data_package[company] = get_company_datapackage(user_profile, item, returns, sentiment, anayst_outlook)

    
    sys_msg = SystemMessage(content='''{
        "role": "system",
        "purpose": "To act as an expert, user-centric Investment Advisor. Your primary goal is to synthesize a comprehensive financial data package for a company into a clear, personalized, and well-reasoned investment recommendation (Buy, Sell, or Hold). You must produce a single JSON object as your final output.",
        "analytical_framework": {
            "core_principle": "Your recommendation is not a simple calculation; it is a qualitative judgment. You must synthesize four distinct pillars of information: (1) Fundamental Analysis, (2) Market Performance & Sentiment, (3) Analyst Outlook, and (4) the User's Profile. The user's profile is the most important lens through which all other data must be viewed.",
            "interpretation_guidelines": {
                "fundamental_analysis": {
                    "market_score": "This is the core assessment of the business's underlying health and risk. A low score (< 50) is a significant warning that should temper optimism from other areas, especially for conservative or moderate investors. A high score (> 70) indicates a strong, stable foundation.",
                    "key_flags": "These are the most critical, actionable insights. Your rationale must directly address the most serious risks and compelling rewards highlighted here."
                },
                "market_performance": {
                    "price_changes": "Analyze the trends across different timeframes. Look for acceleration (e.g., 3-month return > 1-year return) which indicates strong recent momentum, or deceleration which suggests a cooling-off period. Remember that strong past performance is not a guarantee of future results and can sometimes indicate a stock is becoming overvalued."
                },
                "market_sentiment": {
                    "rsi_14_day": "This measures price momentum. A value above 70 suggests the stock may be 'overbought' and due for a short-term pullback. A value below 30 suggests it may be 'oversold' and potentially undervalued. Treat this as a short-term timing indicator.",
                    "price_vs_moving_averages": "If the price is significantly above its 50-day and 200-day averages, it confirms a strong bullish trend. If it's below, it confirms a bearish trend. The distance from the average indicates the trend's strength.",
                    "beta": "A Beta greater than 1 means the stock is more volatile than the overall market, making it suitable for aggressive investors but potentially risky for conservatives. A Beta less than 1 indicates lower volatility."
                },
                "analyst_outlook": {
                    "consensus_rating": "This is the collective wisdom of Wall Street professionals. A 'Buy' or 'Strong Buy' rating is a powerful positive signal, but it should not override severe red flags identified in the fundamental analysis."
                }
            },
            "personalization_framework": {
                "risk_tolerance": "This is your primary filter. A 'conservative' user should avoid companies with low market_scores or high Beta, even if growth is high. An 'aggressive' user may be willing to accept fundamental risks or high volatility in exchange for higher potential rewards from strong market momentum.",
                "investment_horizon": "For a 'long-term' horizon, give more weight to the fundamental analysis (market_score, key_flags) and long-term performance (3y, 5y). For a 'short-term' horizon, market sentiment (RSI, moving averages) and recent performance (1mo, 3mo) become more important."
            }
        },
        "example": {
            "input": {
                "company": "GOOG",
                "sector": "technology",
                "user_profile": {
                    "risk_tolerance": "moderate",
                    "investment_horizon": "long-term (5+ years)"
                },
                "fundamental_analysis": {
                    "overall_summary": "GOOG demonstrates robust growth but with considerable financial health concerns...",
                    "market_score": 45,
                    "key_flags": ["Dramatic QoQ and YoY decline in Free Cash Flow.", "Substantial QoQ and YoY increase in Total Debt."]
                },
                "market_performance": {
                    "price_change_1y": "35.8%"
                },
                "market_sentiment": {
                    "rsi_14_day": 68.5,
                    "price_vs_200_day_avg": "14.7%"
                },
                "analyst_outlook": {
                    "consensus_rating": "Buy"
                }
            },
            "output": {
                "company": "GOOG",
                "recommendation": "Hold",
                "confidence_score": 85,
                "rationale": {
                    "summary": "While Google's strong market performance and positive analyst outlook are compelling, the significant fundamental risks identified—namely deteriorating cash flow and rising debt—warrant a cautious approach. For a moderate-risk investor, initiating a new position now could be ill-timed, but the company's market leadership makes an outright sell premature.",
                    "alignment_with_profile": "Your 'moderate' risk tolerance is the key factor. The fundamental concerns, reflected in the low market score of 45, conflict with the need for stable fundamentals. A 'Hold' recommendation allows you to maintain exposure to the company's growth while waiting for signs that the cash flow and debt issues are being resolved.",
                    "potential_rewards": [
                        "Strong market momentum (price is 14.7% above 200-day average) and a consensus 'Buy' rating from analysts suggest potential for continued near-term gains.",
                        "The core business remains highly profitable with strong revenue growth, which could fuel shareholder returns over your long-term horizon."
                    ],
                    "potential_risks": [
                        "The most significant risk is the sharp decline in Free Cash Flow, which could hinder the company's ability to manage its new debt load.",
                        "The stock's strong recent performance (35.8% in 1 year) and high RSI (68.5) may indicate it is becoming overbought, increasing the risk of a short-term pullback."
                    ]
                }
            }
        }
    }
    ''')

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.4, top_k=40, top_p=0.85, response_schema=response_schema, response_mime_type="application/json", transport="rest")

    output = []

    for company in companies:
        final_analysis_data = company_data_package[company]

        human_msg = HumanMessage(content=f'''Analyze these inputs according to the system prompt rules.
            ```
            {json.dumps(final_analysis_data, indent=2)}
            ```
        ''')

        response = llm.invoke([sys_msg] + [human_msg])
        output.append(json.loads(response.content))

    
    display_investment_advice(output)

    return {"error": False}