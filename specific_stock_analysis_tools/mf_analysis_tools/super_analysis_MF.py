from numpy import nan
from tools.sector_returns import specific_sector_returns
from tools.financials import get_financial_news
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
import json
from rich.panel import Panel
from rich.console import Console, Group
from rich.text import Text
from rich.table import Table
from specific_stock_analysis_tools.mf_analysis_tools.yahooquery_MF import gather_yahooquery_mf_data



response_schema = {
    "type": "object",
    "properties": {
        "fund_name": {
            "type": "string",
            "description": "The name of the fund."
        },
        "recommendation": {
            "type": "string",
            "description": "The final, clear investment recommendation. Must be one of three values: 'Suitable', 'Not Suitable', or 'Consider with Caution'."
        },
        "confidence_score": {
            "type": "number",
            "description": "A score (0-100) indicating the model's confidence in its recommendation based on the data provided."
        },
        "rationale": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "A concise summary explaining the core logic behind the recommendation, balancing the fund's strengths and weaknesses against the user's profile."
                },
                "alignment_with_profile": {
                    "type": "string",
                    "description": "A personalized explanation of how the fund's characteristics specifically align with (or diverge from) the user's risk tolerance, horizon, and goals."
                },
                "key_positives": {
                    "type": "array",
                    "items": {
                        "type": "string" 
                    },
                    "description": "A bulleted list of the most compelling reasons to consider this fund, referencing specific data points like top-tier performance, positive alpha, or a good valuation."
                },
                "key_concerns": {
                    "type": "array",
                    "items": { 
                        "type": "string" 
                    },
                    "description": "A bulleted list of the most significant risks or drawbacks, referencing specific data like high volatility, high expenses, or over-concentration in a single sector."
                }
            },
            "required": ["summary", "alignment_with_profile", "key_positives", "key_concerns"]
        }
    },
    "required": ["fund_name", "recommendation", "confidence_score", "rationale"]
}


def get_metric_data_package(long_name, valuation_measures, annual_returns, trailing_returns, rank_in_category, risk_analysis, sector_weightings, sector_returns, user_profile, financial_news_summary):
    data_package = {
        "name": long_name,
        "user_profile": user_profile,
        "valuation_and_style": valuation_measures,
        "financial_news_summary": financial_news_summary,
        "performance": {
            "annual_returns": annual_returns,
            "trailing_returns": trailing_returns,
            "rank_in_category": rank_in_category
        },
        "risk_analysis": risk_analysis,
        "portfolio_composition": {
            "sector_weightings": sector_weightings,
            "sector_returns": sector_returns
        }
    }

    return data_package


def display_investment_advice(analyzed_items):
    """
    Takes a list of analyzed items (conforming to the new schema) and 
    formats them into a structured, visually appealing layout in the console.
    """
    console = Console()

    for item in analyzed_items:
        # --- Safely extract data from the new schema ---
        company = item.get("fund_name", "N/A")
        recommendation = item.get("recommendation", "N/A")
        rationale = item.get("rationale", {})
        
        summary = rationale.get("summary", "No summary provided.")
        alignment = rationale.get("alignment_with_profile", "No profile alignment provided.")
        rewards = rationale.get("key_positives", [])
        risks = rationale.get("key_concerns", [])

        # --- Style the recommendation ---
        if recommendation.lower() == "suitable":
            rec_style = "bold green"
        elif recommendation.lower() == "not suitable":
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

def analyze_MF(tickers: dict[str, str], state) -> str:
    """
    To analyze a list of Mutual Funds.

    Args
        companies: List of mutual funds you want to analyze
    """
    console = Console()
    # console.print("Generating investment advice...", style="dim italic")

    # tickers = get_tickers(companies)
    fund_data = gather_yahooquery_mf_data(tickers)

    # fund_data = state.get("fund_data", {})

    if(not fund_data):
        return {
            "error": True
        }
    
    funds = list(fund_data.keys())

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.4, top_p=0.85, top_k=40, response_schema=response_schema, response_mime_type="application/json", transport="rest")
    sys_message = SystemMessage(content="""{
        "role": "system",
        "purpose": "To act as an expert Mutual Fund Advisor. Your primary task is to synthesize a detailed financial data package for a mutual fund into a personalized investment recommendation ('Suitable', 'Not Suitable', or 'Consider with Caution') for a user. Your analysis MUST be based on a comparative assessment of the fund against its category benchmarks where available.",
        "analytical_framework": {
            "core_principle": "A mutual fund is judged by its performance relative to its peers and its alignment with an investor's goals. Your entire analysis must be built on comparing the 'fund' data against the 'category' data provided. The user's profile is the ultimate filter for your final recommendation.",
            "interpretation_guidelines": {
                "valuation_and_style": {
                    "guidance": "Compare the fund's valuation ratios (e.g., 'fund_pe_ratio') to its category's ('category_pe_ratio'). A lower P/E or P/B ratio than the category suggests a 'value' tilt. A higher earnings growth rate suggests a 'growth' tilt. Use this to determine if the fund's investment style aligns with its stated category."
                },
                "performance": {
                    "guidance": "Performance is paramount. Focus on three key areas: (1) **Long-Term Outperformance**: Check if the fund's 3-year and 5-year 'trailing_returns' consistently beat the category. (2) **Consistency**: Look at the 'annual_returns' to see if the fund beats its category in most years. (3) **Peer Ranking**: The 'rank_in_category' is a critical summary. Consistently ranking in the top quartile (e.g., rank < 25) is a strong positive signal."
                },
                "risk_analysis": {
                    "guidance": "Analyze risk-adjusted returns. The key metrics are: **Alpha**: A positive Alpha indicates the fund manager is adding value beyond the market's movement; higher is better. **Sharpe Ratio**: This measures return per unit of risk; a higher Sharpe Ratio than the category is a strong sign of superior risk management. **Beta**: A Beta near 1.0 means the fund moves with the market; > 1.0 is more volatile, < 1.0 is less volatile. Compare the fund's Beta to the user's risk tolerance."
                },
                "portfolio_composition": {
                    "guidance": "Analyze the fund's strategy. Look at the 'sector_weightings'. Is the fund making a concentrated bet on a particular sector? Compare this to the 'sector_returns' data. A heavy weighting in a sector with strong recent returns can explain good performance but also indicates concentration risk."
                },
                "financial_news_analysis": {
                    "guidance": "This is your qualitative overlay. You MUST analyze the provided 'financial_news' summary to identify catalysts or headwinds that are not reflected in the quantitative data. Look for news about: (1) Changes in fund management, (2) Shifts in the fund's investment strategy, (3) Major inflows or outflows of assets, or (4) Significant news impacting the fund's top holdings or heavily-weighted sectors. Use these findings to add context to your 'key_positives' and 'key_concerns'."
                }
            },
            "data_handling_rules": {
                "missing_category_data": "Sometimes, 'category' data for comparison will be absent or null. In this scenario, do not heavily penalize the fund. State clearly that a direct peer comparison is not possible. Shift your analysis to focus on the fund's absolute metrics: its own historical performance, its risk-adjusted returns (Sharpe Ratio), its volatility (Beta), and its alignment with the user's profile on its own merits.",
                "return_value_format": "IMPORTANT: All return values in the input data (e.g., trailing_returns, annual_returns) are provided in decimal format. For example, a value of `0.3081` represents a `30.81%` return. You must interpret these correctly and present them as percentages in your final analysis to ensure clarity for the user."
            },
            "personalization_framework": {
                "risk_tolerance": "This is the primary filter. A fund with a high 'risk_rating' and Beta > 1.0 is generally unsuitable for a 'conservative' investor, even if returns are high. Conversely, an 'aggressive' investor might find this profile attractive.",
                "investment_horizon": "For a 'long-term' horizon, prioritize consistent 5-year and 10-year performance and a strong Sharpe Ratio. For shorter horizons, recent performance (1-year return and rank) might be more relevant, but with higher risk.",
                "investment_goal": "If the goal is 'wealth_creation', a fund with high growth, positive Alpha, and higher risk might be suitable. If the goal is 'capital_preservation', a fund with a lower Beta and a history of smaller drawdowns is preferable."
            }
        },
        "example": {
            "input": {
                "user_profile": {
                    "risk_tolerance": "aggressive",
                    "investment_horizon": "long-term (7+ years)",
                    "investment_goal": "wealth_creation"
                },
                "data_package": {
                    "name": "Axis Small Cap Fund Direct Growth",
                    "performance": {
                        "trailing_returns": { "fund": { "fiveYear": 0.3081 }, "category": { "fiveYear": 0.2500 } },
                        "rank_in_category": { "fiveYear": 1 }
                    },
                    "risk_analysis": {
                        "risk_rating": 5,
                        "5y_statistics": { "fund": { "alpha": 8.4, "beta": 1.02, "sharpeRatio": 1.32 }, "category": { "alpha": 2.5, "beta": 1.0, "sharpeRatio": 1.10 } }
                    },
                    "portfolio_composition": {
                        "sector_weightings": [{ "sector": "Industrials", "weight": 0.3562 }]
                    }
                }
            },
            "output": {
                "fund_name": "Axis Small Cap Fund Direct Growth",
                "recommendation": "Suitable",
                "confidence_score": 95,
                "rationale": {
                    "summary": "This fund is an excellent fit for an aggressive, long-term investor focused on wealth creation. It has demonstrated exceptional, category-beating performance over the long term with superior risk-adjusted returns, although its high-risk rating and concentration in the Industrials sector must be acknowledged.",
                    "alignment_with_profile": "Your 'aggressive' risk tolerance and 'long-term' horizon align perfectly with this fund's profile. Its high risk rating (5/5) and Beta (1.02) are matched by its potential for high returns, suitable for your 'wealth_creation' goal. The fund's proven ability to generate significant Alpha (8.4 vs category's 2.5) indicates strong management skill, justifying the risk.",
                    "key_positives": [
                        "Consistent top-tier performer, ranking in the top 1% of its category over 5 years with a 30.81% annualized return.",
                        "Generates significant Alpha (8.4), indicating the fund manager has historically provided value beyond market returns.",
                        "Superior risk-adjusted returns, evidenced by a higher Sharpe Ratio (1.32) compared to its category (1.10)."
                    ],
                    "key_concerns": [
                        "Carries a high risk rating (5/5) and is slightly more volatile than the market (Beta 1.02), making it susceptible to larger drawdowns during market downturns.",
                        "Significant concentration in the Industrials sector (35.6%) means the fund's performance is heavily tied to the outlook of that specific industry."
                    ]
                }
            }
        }
    }""")

    output = []

    for fund in funds:
        fund_performance = fund_data[fund].get("fund_performance", {})
        fund_sector_weightings = fund_data[fund].get("fund_sector_weightings", {})
        fund_valuation_measures = fund_data[fund].get("fund_valuation_measures", {})
        additional_info = fund_data[fund].get("additional_info", {})

        fund_name = additional_info["longName"] if additional_info["longName"] else additional_info["shortName"]
        financial_news_summary = get_financial_news(fund_name, fund)

        sector_weighting_list = []
        sector_list = []
        for sector, weight in fund_sector_weightings.items():
            sector_list.append(sector.replace("_", "-"))
            sector_weighting_list.append({
                "sector": sector,
                "weight": weight
            })

        sector_returns = specific_sector_returns(sector_list)

        risk_analysis = {
            "risk_rating": fund_performance.get("riskOverviewStatistics", {}).get("riskRating", nan),
            "3y_statistics": {
                "fund": {},
                "category": {}
            },
            "5y_statistics": {
                "fund": {},
                "category": {}
            },
            "10y_statistics": {
                "fund": {},
                "category": {}
            }
        }
        for risk_statistic in fund_performance.get("riskOverviewStatistics", {}).get("riskStatistics", []):
            if(risk_statistic.get("year", nan) == "3y"):
                risk_analysis["3y_statistics"]["fund"] = risk_statistic
            elif(risk_statistic.get("year", nan) == "5y"):
                risk_analysis["5y_statistics"]["fund"] = risk_statistic
            elif(risk_statistic.get("year", nan) == "10y"):
                risk_analysis["10y_statistics"]["fund"] = risk_statistic

        for risk_statistic in fund_performance.get("riskOverviewStatisticsCat", {}).get("riskStatisticsCat", []):
            if(risk_statistic.get("year", nan) == "3y"):
                risk_analysis["3y_statistics"]["category"] = risk_statistic
            elif(risk_statistic.get("year", nan) == "5y"):
                risk_analysis["5y_statistics"]["category"] = risk_statistic
            elif(risk_statistic.get("year", nan) == "10y"):
                risk_analysis["10y_statistics"]["category"] = risk_statistic

        
        annual_returns = {
            "fund": {},
            "category": {}
        }
        year = -1
        for returns in fund_performance["annualTotalReturns"]["returns"]:
            year = returns.get("year")
            annual_returns["fund"][year] = returns.get("annualValue", nan)

        for returns in fund_performance["annualTotalReturns"]["returnsCat"]:
            if(returns.get("year") < year):
                break
            annual_returns["category"][returns.get("year")] = returns.get("annualValue", nan)

        
        trailing_returns = {
            "fund": fund_performance.get("trailingReturns", {}),
            "category": fund_performance.get("trailingReturnsCat", {})
        }

        rank_in_category = fund_performance.get("rankInCategory", {})


        valuation_measures = {
            "fund_pe_ratio": fund_valuation_measures.get("priceToEarnings", nan),
            "category_pe_ratio": fund_valuation_measures.get("priceToEarningsCat", nan),
            "fund_pb_ratio": fund_valuation_measures.get("priceToBook", nan),
            "category_pb_ratio": fund_valuation_measures.get("priceToBookCat", nan),
            "fund_median_market_cap": fund_valuation_measures.get("medianMarketCap", nan),
            "category_median_market_cap": fund_valuation_measures.get("medianMarketCapCat", nan),
            "fund_3yr_earnings_growth": fund_valuation_measures.get("threeYearEarningsGrowth", nan),
            "category_3yr_earnings_growth": fund_valuation_measures.get("threeYearEarningsGrowthCat", nan)
        }

        long_name = additional_info.get("longName", "N/A")
        user_profile = state.get("user_profile", {})

        data_package = get_metric_data_package(long_name, valuation_measures, annual_returns, trailing_returns, rank_in_category, risk_analysis, sector_weighting_list, sector_returns, user_profile, financial_news_summary)

        human_msg = HumanMessage(content=f"""Please analyze the provided input according to the guidelines given in the system prompt
            ```
            {json.dumps(data_package, indent=2)}
            ```
        """)

        response = llm.invoke([sys_message] + [human_msg])

        item = json.loads(response.content)
        item["fund_name"] = fund
        output.append(item)

    display_investment_advice(output)

    return "Mutual fund(s) have been analyzed successfully"

        
        

