from langchain_core.messages import HumanMessage, SystemMessage
from numpy import nan
from langchain_google_genai import ChatGoogleGenerativeAI
import json
from tools.financials import get_financial_news
import numpy as np
import pandas as pd
from currency_converter import CurrencyConverter 
from millify import millify
from rich.console import Console

def _safe_get(df, index, column, default=nan):
    """Safely get a value from a DataFrame, handling out-of-bounds and missing columns."""
    try:
        if -df.shape[0] <= index < df.shape[0] and column in df.columns:
            return df.iloc[index][column]
        return default
    except (IndexError, KeyError):
        return default

def _calculate_cagr(end_value, start_value, years):
    """Calculates Compound Annual Growth Rate."""
    if start_value is None or end_value is None or start_value == 0 or years <= 0:
        return nan
    
    if np.sign(start_value) != np.sign(end_value):
        return nan
    return (abs(end_value / start_value)) ** (1 / years) - 1

def _calculate_change(current, previous):
    """Calculates percentage change, handling NaN and zero division."""
    if current is None or previous is None or previous == 0:
        return nan
    return (current - previous) / abs(previous)

def get_metric_datapackage(
    metric_name, display_name, unit_type, company_currency, c,
    q_df, a_df, ttm_is_df, ttm_cf_df, ttm_vm_df, sector_key
):
    """
    Analyzes a single metric across TTM, Quarterly, and Annual dataframes
    to produce the final structured data package.
    """
    package = {
        "displayName": display_name,
        "sector": sector_key,
        "ttmValue": "N/A",
        "unit": "USD" if unit_type == 'currency' else 'ratio',
        "quarterly": {"history": {}, "trends": {}},
        "annual": {"history": {}, "trends": {}}
    }

    
    ttm_value = nan
    ttm_source_df = pd.DataFrame()
    if metric_name in ttm_is_df.columns:
        ttm_source_df = ttm_is_df
    elif metric_name in ttm_cf_df.columns:
        ttm_source_df = ttm_cf_df
    elif metric_name in ttm_vm_df.columns:
        ttm_source_df = ttm_vm_df
    
    if not ttm_source_df.empty:
        ttm_value = _safe_get(ttm_source_df, -1, metric_name)
    
    if pd.isna(ttm_value):
        ttm_value = _safe_get(q_df, -1, metric_name)

    if not pd.isna(ttm_value):
        if unit_type == 'currency':
            converted_val = c.convert(ttm_value, company_currency, 'USD')
            package['ttmValue'] = millify(round(converted_val, 2)) if not pd.isna(converted_val) else "N/A"
        else:
            package['ttmValue'] = round(ttm_value, 2)
            package['unit'] = 'x'

    if not q_df.empty and metric_name in q_df.columns:
        q_df['asOfDate'] = pd.to_datetime(q_df['asOfDate'])
        q_df = q_df.sort_values('asOfDate').reset_index(drop=True)
        
        last_5_quarters = q_df.tail(5)
        for _, row in last_5_quarters.iterrows():
            date_str = row['asOfDate'].strftime('%Y-%m-%d')
            value = row[metric_name]
            if not pd.isna(value):
                package['quarterly']['history'][date_str] = millify(c.convert(value, company_currency, 'USD'), precision=2)

        if len(q_df) > 1:
            q0_row = q_df.iloc[-1]
            q0_date = q0_row['asOfDate']
            q0_val = q0_row[metric_name]

            q1_date_target = q0_date - pd.DateOffset(months=3)
            q1_row = q_df[q_df['asOfDate'].dt.month == q1_date_target.month]
            q1_val = q1_row[metric_name].iloc[-1] if not q1_row.empty else nan
            
            q4_date_target = q0_date - pd.DateOffset(years=1)
            q4_row = q_df[q_df['asOfDate'] == q4_date_target]
            q4_val = q4_row[metric_name].iloc[0] if not q4_row.empty else nan
            
            qoq = _calculate_change(q0_val, q1_val)
            yoy = _calculate_change(q0_val, q4_val)

            package['quarterly']['trends']['qoq_change_percent'] = round(qoq * 100, 2) if not pd.isna(qoq) else nan
            package['quarterly']['trends']['yoy_change_percent'] = round(yoy * 100, 2) if not pd.isna(yoy) else nan
            
    if not a_df.empty and metric_name in a_df.columns:
        a_df['asOfDate'] = pd.to_datetime(a_df['asOfDate'])
        a_df = a_df.sort_values('asOfDate').reset_index(drop=True)

        last_5_years = a_df.tail(5)
        for _, row in last_5_years.iterrows():
            date_str = row['asOfDate'].strftime('%Y-%m-%d')
            value = row[metric_name]
            if not pd.isna(value):
                package['annual']['history'][date_str] = millify(c.convert(value, company_currency, 'USD'), precision=2)

        if len(a_df) >= 4:
            end_val = _safe_get(a_df, -1, metric_name)
            start_val_3y = _safe_get(a_df, -4, metric_name)
            cagr_3y = _calculate_cagr(end_val, start_val_3y, 3)
            package['annual']['trends']['cagr_3_year'] = round(cagr_3y * 100, 2) if not pd.isna(cagr_3y) else nan

        if len(a_df) >= 6:
            end_val = _safe_get(a_df, -1, metric_name)
            start_val_5y = _safe_get(a_df, -6, metric_name)
            cagr_5y = _calculate_cagr(end_val, start_val_5y, 5)
            package['annual']['trends']['cagr_5_year'] = round(cagr_5y * 100, 2) if not pd.isna(cagr_5y) else nan

    return package

def analyze_EQUITY(equity_data):
    console = Console()
    c = CurrencyConverter()

    console.print("Analyzing financial instruments...", style="dim italic")

    income_statement = equity_data.get("income_statement", pd.DataFrame)
    balance_sheet = equity_data.get("balance_sheet", pd.DataFrame)
    valuation_measures = equity_data.get("valuation_measures", pd.DataFrame)
    cashflow_statement = equity_data.get("cashflow_statement", pd.DataFrame)
    companies = list(income_statement.keys())
    financial_data = equity_data.get("financial_data", {})
    additional_info = equity_data.get("additional_info", {})
    
    final_analysis_data = {}

    metrics_to_analyze = {
        
        "PeRatio": {"displayName": "P/E Ratio", "unit_type": "ratio"},
        "PbRatio": {"displayName": "P/B Ratio", "unit_type": "ratio"},
        "PsRatio": {"displayName": "P/S Ratio", "unit_type": "ratio"},
        "EnterprisesValueEBITDARatio": {"displayName": "EV/EBITDA Ratio", "unit_type": "ratio"},
        "PegRatio": {"displayName": "PEG Ratio", "unit_type": "ratio"},    
        "TotalRevenue": {"displayName": "Total Revenue", "unit_type": "currency"},
        "GrossProfit": {"displayName": "Gross Profit", "unit_type": "currency"},
        "OperatingIncome": {"displayName": "Operating Income", "unit_type": "currency"},
        "NetIncomeCommonStockholders": {"displayName": "Net Income", "unit_type": "currency"},
        "DilutedEPS": {"displayName": "Diluted EPS", "unit_type": "currency"},
        "OperatingCashFlow": {"displayName": "Operating Cash Flow", "unit_type": "currency"},
        "FreeCashFlow": {"displayName": "Free Cash Flow", "unit_type": "currency"},
        "TotalDebt": {"displayName": "Total Debt", "unit_type": "currency"},
        "StockholdersEquity": {"displayName": "Stockholders Equity", "unit_type": "currency"},
    }

    response_schema = {
        "type": "object",
        "properties": {
            "company": {
                "type": "string",
                "description": "Ticker of the company being analyzed. Don't use the company name even if you know it. Just use the ticker as passed with the input"
            },
            "sector": {
                "type": "string",
                "description": "The company's industry sector, provided in the input."
            },
            "thematic_analysis": {
                "type": "object",
                "properties": {
                    "valuation": {
                        "type": "string",
                        "description": "Analysis of the company's valuation. Must focus on the TRENDS (QoQ, YoY) of key valuation metrics, interpreting what these trends imply about investor sentiment and market expectations."
                    },
                    "profitability_and_growth": {
                        "type": "string",
                        "description": "Analysis of profitability and growth. Must focus on the TRENDS of revenue, earnings, and margins, explaining whether growth is accelerating or decelerating and if it's translating to the bottom line."
                    },
                    "financial_health": {
                        "type": "string",
                        "description": "Analysis of the company's financial stability and risk. Must focus on trends in cash flow, debt, and equity, assessing the company's liquidity, solvency, and ability to fund operations."
                    }
                }
            },
            "overall_summary": {
                "type": "string",
                "description": "A concise, top-level summary (2-3 sentences) that encapsulates the most critical findings from the thematic analysis, balancing strengths and weaknesses."
            },
            "key_flags": {
                "type": "array",
                "items": {
                    "type": "string",
                    "description": "A short, bulleted list of the most significant strengths, weaknesses, or risks identified in the analysis. Frame these around trends (e.g., 'Strengthening operating margins for three consecutive quarters')."
                }
            },
            "market_score": {
                "type": "number",
                "description": "A holistic score (0-100) reflecting the overall strength of the investment thesis. This is a qualitative judgment based on the entire analysis, not a formula. A high score requires a healthy balance across all themes."
            },
            "confidence": {
                "type": "number",
                "description": "Confidence level (0-100) in the analysis, based on the completeness of the provided data. Lower the score if key trends (QoQ, YoY, CAGR) are missing."
            }
        },
        "required": ["company", "sector", "thematic_analysis", "overall_summary", "key_flags", "market_score", "confidence"]
    }

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.4, top_p=0.85, top_k=40, response_schema=response_schema, response_mime_type="application/json", transport="rest")

    sys_message = SystemMessage(content="""{
            "role": "system",
            "purpose": "To act as an expert financial analyst. Your primary goal is to synthesize pre-processed financial data into a high-quality, thematic, and trend-based market analysis for a given company. The analysis must be similar in style and quality to that of a top-tier financial news provider.",
            "analytical_framework": {
                "general_principles": [
                    "**Trend-Based Narrative is Mandatory**: Your entire analysis must be built around trends. For each metric discussed, you must reference its QoQ and/or YoY change. Use interpretive language like 'strengthened,' 'declined,' 'accelerated,' 'indicates growing investor confidence,' or 'reflects effective cost management.'",
                    "**Synthesize, Don't List**: Do not simply list metric values. Weave the data points from the provided JSON into a coherent narrative within each theme. Explain the 'so what' of each trend.",
                    "**Adhere to Thematic Structure**: Your analysis must be organized into the three themes: Valuation, Profitability & Growth, and Financial Health. Do not mix them.",
                    "**Use Provided Data Only**: Base your analysis exclusively on the structured data package provided for each company. Do not use outside knowledge."
                    "**Integrate News Context**: You must use the 'financial_news_summary' to provide qualitative context that explains the 'why' behind the quantitative trends. For example, connect a rise in revenue directly to a product launch mentioned in the news."
                ],
                "sector_focus_metrics": {
                    "description": "While all metrics are important, you must give special emphasis to the following key indicators based on the company's sector.",
                    "financial-services": ["PbRatio", "TotalDebt", "StockholdersEquity", "NetIncomeCommonStockholders", "DilutedEPS"],
                    "technology": ["PeRatio", "PsRatio", "PegRatio", "TotalRevenue", "OperatingIncome", "FreeCashFlow"],
                    "consumer-cyclical": ["PsRatio", "GrossProfit", "OperatingCashFlow", "TotalDebt", "StockholdersEquity"],
                    "consumer-defensive": ["PeRatio", "GrossProfit", "OperatingCashFlow", "TotalDebt", "StockholdersEquity"],
                    "industrials": ["EnterprisesValueEBITDARatio", "PbRatio", "TotalDebt", "OperatingCashFlow", "FreeCashFlow"],
                    "basic-materials": ["EnterprisesValueEBITDARatio", "PbRatio", "OperatingCashFlow", "TotalDebt"],
                    "healthcare": ["PeRatio", "PsRatio", "OperatingIncome", "FreeCashFlow"],
                    "energy": ["EnterprisesValueEBITDARatio", "PbRatio", "OperatingCashFlow", "TotalDebt"],
                    "real-estate": ["PbRatio", "TotalDebt", "OperatingCashFlow"],
                    "utilities": ["PeRatio", "TotalDebt", "OperatingCashFlow"],
                    "communication-services": ["PeRatio", "EnterprisesValueEBITDARatio", "TotalRevenue", "FreeCashFlow", "TotalDebt"]
                }
            },
            "scoring_guidance": {
                "principle": "The 'market_score' is not a mathematical calculation but a qualitative assessment of the overall investment thesis based on your analysis. It reflects the balance of opportunity versus risk. The financial_news_summary acts as a critical qualitative overlay; strongly positive news can push a score towards the higher end of its range, while significant negative news can push it lower or justify dropping it into a weaker category.",
                "strong_score (70-100)": "Requires positive trends across MOST themes. Strong growth must be supported by healthy profitability and a solid financial position. Valuation must be reasonable.",
                "moderate_score (40-69)": "Indicates a mixed picture. The company may have strong growth but also high leverage, or great profitability but slowing momentum. The analysis should reflect this trade-off.",
                "weak_score (0-39)": "Warranted if there are significant red flags in any single theme, such as negative cash flow, unsustainable debt, declining margins, or extreme overvaluation, even if other themes look positive."
            },
            "confidence_rules": {
                "high (90-100)": "All key metrics and their QoQ, YoY, and CAGR trends are present.",
                "moderate (60-89)": "Most key metrics are present, but some trends (e.g., QoQ) might be missing due to data gaps.",
                "low (0-59)": "Significant gaps in recent quarterly data prevent the calculation of key YoY or TTM trends. The analysis must mention this limitation."
            },
            "example_output": {
                "company": "IDI.NY", # Use only the ticker name as passed in input. Even if you know the company name or it is mentioned anywhere, don't use it.
                "sector": "technology",
                "overall_summary": "Innovatech Dynamics showcases a robust growth profile, with revenue accelerating year-over-year. This top-line strength is complemented by expanding operating margins, indicating effective cost control. However, valuation has become stretched, with its P/E ratio rising significantly over the last two quarters, and a high reliance on debt poses a notable risk to its financial stability.",
                "thematic_analysis": {
                    "valuation": "Investor sentiment for Innovatech has strengthened considerably, evidenced by its P/E ratio increasing to 35.2x from 28.5x in the prior quarter. Similarly, its EV/EBITDA ratio trended upward, suggesting the market is pricing in high future growth expectations. While positive, these elevated multiples warrant caution as they may be outpacing fundamental performance.",
                    "profitability_and_growth": "The company's growth trajectory is impressive, with year-over-year revenue growth hitting 22.5%, an acceleration from 18.7% in the same quarter last year. More importantly, this growth is profitable; the operating margin improved to 25.1% from 23.8% sequentially, demonstrating scalable operational efficiency.",
                    "financial_health": "While profitable, the company's balance sheet reveals a key risk. Total Debt to Stockholders' Equity has risen to 1.8 from 1.5 a year ago, indicating increased leverage. On a positive note, Operating Cash Flow remains strong and grew 15% YoY, confirming that earnings are being converted to cash, providing a buffer to service its debt obligations."
                },
                "key_flags": [
                    "Accelerating YoY revenue growth",
                    "Improving operating margins reflect efficiency",
                    "Valuation multiples (P/E, EV/EBITDA) are becoming stretched",
                    "Increasing debt-to-equity ratio poses a financial risk"
                    "Positive news catalyst: Recent AI product launch well-received"
                ],
                "market_score": 65,
                "confidence": 95
            }
        }
    """)

    output = []

    for company in companies:
        console.print(f"Processing data for [bold green]{company}[/bold green]...", style="dim italic")
        company_currency = financial_data.get(company, {}).get("financialCurrency", "USD")

        sector_key = additional_info[company].get("sectorKey", nan)
        
        is_df = income_statement[company]
        bs_df = balance_sheet[company]
        cf_df = cashflow_statement[company]
        vm_df = valuation_measures[company]
        
        q_is_df = is_df[is_df['periodType'] == '3M'].copy() if not is_df.empty else pd.DataFrame()
        q_bs_df = bs_df[bs_df['periodType'] == '3M'].copy() if not bs_df.empty else pd.DataFrame()
        q_cf_df = cf_df[cf_df['periodType'] == '3M'].copy() if not cf_df.empty else pd.DataFrame()
        q_vm_df = vm_df[vm_df['periodType'] == '3M'].copy() if not vm_df.empty else pd.DataFrame()
        
        a_is_df = is_df[is_df['periodType'] == '12M'].copy() if not is_df.empty else pd.DataFrame()
        a_bs_df = bs_df[bs_df['periodType'] == '12M'].copy() if not bs_df.empty else pd.DataFrame()
        a_cf_df = cf_df[cf_df['periodType'] == '12M'].copy() if not cf_df.empty else pd.DataFrame()
        
        ttm_is_df = is_df[is_df['periodType'] == 'TTM'].copy() if not is_df.empty else pd.DataFrame()
        ttm_cf_df = cf_df[cf_df['periodType'] == 'TTM'].copy() if not cf_df.empty else pd.DataFrame()
        ttm_vm_df = vm_df[vm_df['periodType'] == 'TTM'].copy() if not vm_df.empty else pd.DataFrame()

        company_results = {}
        
        for metric_name, details in metrics_to_analyze.items():
            q_df = pd.DataFrame()
            if metric_name in q_is_df.columns: q_df = q_is_df
            elif metric_name in q_bs_df.columns: q_df = q_bs_df
            elif metric_name in q_cf_df.columns: q_df = q_cf_df
            elif metric_name in q_vm_df.columns: q_df = q_vm_df
            
            a_df = pd.DataFrame()
            if metric_name in a_is_df.columns: a_df = a_is_df
            elif metric_name in a_bs_df.columns: a_df = a_bs_df
            elif metric_name in a_cf_df.columns: a_df = a_cf_df

            company_results[metric_name] = get_metric_datapackage(
                metric_name, details['displayName'], details['unit_type'], company_currency, c,
                q_df, a_df, ttm_is_df, ttm_cf_df, ttm_vm_df, sector_key
            )


        name = additional_info[company].get("longName", "") if additional_info[company].get("longName", "") else additional_info[company].get("shortName", "")
        financial_news = get_financial_news(name, company)
        company_results["financial_news_summary"] = financial_news
        
        final_analysis_data[company] = company_results

        human_msg = HumanMessage(content=f"""Analyze the provided data package and do an analysis of the company according to the format given in system prompt
            ```
            {json.dumps(final_analysis_data, indent=2)}
            ```                        
        """)

        response = llm.invoke([sys_message] + [human_msg])

        item = json.loads(response.content)
        item["company"] = company

        output.append(item)
    
    return output
