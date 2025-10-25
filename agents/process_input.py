from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
import os
from rich.console import Console
from google.ai.generativelanguage_v1beta.types import Tool as GenAITool

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

api_key = os.getenv("GEMINI_API_KEY")


# For Gemini structured output
response_schema = {
    "type": "object",
    "properties": {
        "analysis": {
            "type": "string",
            "description": "Brief reasoning about classification and entity extraction"
        },
        "classification": {
            "type": "string",
            "enum": ["SPECIFIC_STOCK_ANALYSIS", "GENERAL_PORTFOLIO_RECOMMENDATIONS", "PORTFOLIO_MANAGEMENT", "PORTFOLIO_ANALYSIS"],
            "description": "Classification of user input according to provided options"
        },
        "extracted_entities": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "List of verbatim names, tickers, or sectors extracted from the query"
        },
        "holdings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "default": "",
                        "description": "Name of the company as appearing in the extracted entities"
                    },
                    "price": {
                        "type": "number",
                        "default": 0.0,
                        "description": "Price at which the stock was bought"
                    },
                    "quantity": {
                        "type": "integer",
                        "default": 0,
                        "description": "Quantity of that particular stock which was bought"
                    }
                },
                "required": ["name", "price", "quantity"]
            },
        }
    },
    "required": ["analysis", "classification", "extracted_entities", "holdings"]
}


def parse_user_input(state):

    console = Console()
    console.print("Understanding user input...", style="dim italic")

    user_input = state["messages"][-1]

    tools = [generate_portfolio_report, add_to_database, update_database, list_database, clear_database, get_by_trans, get_database_by_name, delete_database_by_name, delete_database_by_trans, get_sector_industry_recommendation, specific_stock_analysis, screen_stocks, get_financial_news, display_result_for_unknown_prompts]

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", transport="rest")
    llm_with_tools = llm.bind_tools(tools)

    sys_message = SystemMessage(content='''{
        "role": "system",
        "purpose": "To act as an intelligent and precise Tool Router for a comprehensive financial assistant. Your primary function is to analyze a user's query, understand their intent, and select the single best tool to call from the provided list to fulfill their request. You must also extract all necessary parameters for the selected tool.",
        "decision_framework": {
            "core_logic": "Analyze the user's query to determine their primary goal. Match this goal to one and only one tool from the 'tool_guidelines'. Your response MUST be a single tool call.",
            "disambiguation": "If a query is ambiguous (e.g., 'show me apple'), prefer the informational tool ('get_database_by_name') over the action tool ('delete_database_by_name'). Explicit commands like 'sell' or 'buy' are required for action tools.",
            "no_op_rule": "If the query is conversational or does not map to any tool (e.g., 'hello', 'thank you', 'what is the market doing?'), you must call the 'no_op' tool."
        },
        "tool_guidelines": [
            {
                "tool_name": "specific_stock_analysis",
                "description": "Analyzes financial instruments like equities and mutual funds.",
                "triggers": ["analyze", "what do you think of", "tell me about", "performance of", "outlook for"],
                "parameter_extraction": {
                    "companies": "Use the 'entity_handling' rules to extract a list of company names or tickers."
                }
            },
            {
                "tool_name": "screen_stocks",
                "description": "Screens for stocks or funds based on predefined lists or complex custom criteria. This is the primary tool for discovering new investment ideas.",
                "triggers": ["find", "screen for", "show me stocks that", "search for", "look for funds with"],
                "parameter_extraction": {
                    "screener_type": "First, determine the user's intent. If they mention a specific list from the 'predefined_screeners' list (e.g., 'day gainers', 'most actives'), set to 'predefined'. If they mention 'stocks' or 'companies', set to 'equity'. If they mention 'funds', set to 'fund'.",
                    "predefined_screeners": "If the screener_type is 'predefined', extract the canonical screener name from the provided list.",
                    "custom_filters": "If the screener_type is 'equity' or 'fund', you must translate every condition in the user's query into a filter object using the 'screener_parameter_mapping' rules. This is the primary task. Make it an empty list [] if the screener_type is 'predefined'. List should have values only if screener_type is 'equity' or 'fund'",
                    "comparison_type": "Detect if the user wants to combine filters with 'and' (default), 'or' or 'None'. If only one custom_filter is present make it None",
                    "count": "Extract the number of results the user wants, if specified (e.g., 'top 5', '10 stocks'). Default to 10 if not mentioned."
                }
            },
            {
                "tool_name": "get_financial_news",
                "description": "Fetches recent financial news for one or more specific companies, or for the user's entire portfolio if no companies are named.",
                "triggers": ["news", "headlines", "latest updates", "what's happening with", "any news on"],
                "parameter_extraction": {
                    "companies": "Use the 'general_entity_handling' rules to extract a list of company names or tickers from the user's query. If the user mentions 'my portfolio' or asks for general news without naming a specific company, do not populate this parameter. Make it an empty list [] in such cases."
                }
            },
            {
                "tool_name": "display_result_for_unknown_prompts",
                "description": "A fallback tool for handling general conversation, queries outside of finance, or any request that does not fit the other specialized tools. Use this as a last resort to provide a helpful, search-powered answer.",
                "triggers": [
                    "This is the default tool; use it when no other tool is appropriate.",
                    "General conversational phrases (e.g., 'hello', 'who are you?', 'tell me a joke').",
                    "General knowledge or factual questions not related to finance (e.g., 'what is the tallest building?', 'who is the president?').",
                    "Vague or ambiguous prompts where the user's intent is unclear after initial analysis."
                ],
                "parameter_extraction": {
                    "prompt": "You must capture the user's original, unmodified prompt and pass it directly to this tool."
                }
            },
            {
                "tool_name": "get_sector_industry_recommendation",
                "description": "Generates strategic sector and industry recommendations to improve portfolio diversification.",
                "triggers": ["suggest", "recommend", "what should I invest in", "find me opportunities", "diversify my portfolio"],
                "parameter_extraction": {
                    "included_sectors": "Use the 'mapping_guidelines' to find sectors the user wants to focus on.",
                    "excluded_sectors": "Use the 'mapping_guidelines' to find sectors the user wants to avoid."
                }
            },
            {
                "tool_name": "generate_portfolio_report",
                "description": "Generates a PDF report of the user's portfolio.",
                "triggers": ["generate report", "create a pdf", "download my portfolio"]
            },
            {
                "tool_name": "add_to_database",
                "description": "Add new holdings into the user's account.",
                "triggers": ["buy", "add", "purchase"],
                "parameters": {
                    "company": "string",
                    "quantity": "integer",
                    "price": "float"
                }
            },
            {
                "tool_name": "clear_database",
                "description": "Clear all holdings from the user's account.",
                "triggers": ["clear all", "delete all", "reset portfolio", "clear my holdings"]
            },
            {
                "tool_name": "delete_database_by_name",
                "description": "Delete holdings by name from the user's account.",
                "triggers": ["sell", "delete", "remove"],
                "parameters": { "companies": "list[string]" }
            },
            {
                "tool_name": "delete_database_by_trans",
                "description": "Delete a holding using a transaction ID.",
                "triggers": ["delete transaction", "remove transaction", "cancel tx"],
                "parameters": { "transaction_id": "string" }
            },
            {
                "tool_name": "get_by_trans",
                "description": "Find or fetch a holding by its transaction ID.",
                "triggers": ["get transaction", "find transaction", "view tx"],
                "parameters": { "transaction_id": "string" }
            },
            {
                "tool_name": "get_database_by_name",
                "description": "Find or fetch holdings by company name.",
                "triggers": ["get", "show", "view", "find"],
                "parameters": { "companies": "list[string]" }
            },
            {
                "tool_name": "list_database",
                "description": "List or view all holdings in the user's account/display users portfolio",
                "triggers": ["list all", "show all", "view all holdings", "what's in my portfolio"]
            },
            {
                "tool_name": "update_database",
                "description": "Update a particular holding in the user's account using its transaction ID.",
                "triggers": ["update", "change", "modify"],
                "parameters": {
                    "transaction_id": "string",
                    "new_quantity": "integer (optional)",
                    "new_price": "float (optional)"
                }
            }
        ],
        "parameter_extraction_rules": {
            "screener_parameter_mapping": {
                "description": "This is your dictionary for translating user language into valid API parameters for the 'screen_stocks' tool.
                "predefined_screeners": categories = [
                    "advertising_agencies", "aggressive_small_caps", "all_cryptocurrencies_au", "all_cryptocurrencies_ca",
                    "all_cryptocurrencies_eu", "all_cryptocurrencies_gb", "all_cryptocurrencies_in", "all_cryptocurrencies_us",
                    "aluminum", "asset_management", "auto_parts", "beverages_brewers", "biotechnology", "communication_equipment",
                    "confectioners", "conglomerates", "conservative_foreign_funds", "copper", "credit_services",
                    "day_gainers", "day_gainers_americas", "day_gainers_asia", "day_gainers_au", "day_gainers_br",
                    "day_gainers_ca", "day_gainers_de", "day_gainers_dji", "day_gainers_es", "day_gainers_europe",
                    "day_gainers_fr", "day_gainers_gb", "day_gainers_hk", "day_gainers_in", "day_gainers_it",
                    "day_gainers_ndx", "day_gainers_nz", "day_gainers_sg", "day_losers", "day_losers_americas",
                    "day_losers_asia", "day_losers_au", "day_losers_br", "day_losers_ca", "day_losers_de",
                    "day_losers_dji", "day_losers_es", "day_losers_europe", "day_losers_fr", "day_losers_gb",
                    "day_losers_hk", "day_losers_in", "day_losers_it", "day_losers_ndx", "day_losers_nz", "day_losers_sg",
                    "department_stores", "education_training_services", "farm_products", "gold", "grocery_stores",
                    "growth_technology_stocks", "high_yield_bond", "information_technology_services", "insurance_brokers",
                    "lodging", "lumber_wood_production", "medical_instruments_supplies", "mega_cap_hc", "metal_fabrication",
                    "most_actives", "most_actives_americas", "most_actives_asia", "most_actives_au", "most_actives_br",
                    "most_actives_ca", "most_actives_de", "most_actives_dji", "most_actives_es", "most_actives_europe",
                    "most_actives_fr", "most_actives_gb", "most_actives_hk", "most_actives_in", "most_actives_it",
                    "most_actives_ndx", "most_actives_nz", "most_actives_sg", "most_watched_tickers", "ms_basic_materials",
                    "ms_communication_services", "ms_consumer_cyclical", "ms_consumer_defensive", "ms_energy",
                    "ms_financial_services", "ms_healthcare", "ms_industrials", "ms_real_estate", "ms_technology",
                    "ms_utilities", "oil_gas_equipment_services", "oil_gas_refining_marketing", "packaging_containers",
                    "paper_paper_products", "personal_services", "pollution_treatment_controls", "portfolio_anchors",
                    "railroads", "real_estate_development", "recreational_vehicles", "reit_diversified",
                    "reit_healthcare_facilities", "reit_hotel_motel", "reit_industrial", "reit_office", "reit_residential",
                    "reit_retail", "rental_leasing_services", "residential_construction", "resorts_casinos", "restaurants",
                    "scientific_technical_instruments", "security_protection_services", "semiconductor_equipment_materials",
                    "silver", "small_cap_gainers", "solid_large_growth_funds", "solid_midcap_growth_funds", "specialty_chemicals",
                    "top_energy_us", "top_etfs_us", "top_mutual_funds", "top_mutual_funds_au", "top_mutual_funds_br",
                    "top_mutual_funds_ca", "top_mutual_funds_de", "top_mutual_funds_es", "top_mutual_funds_fr",
                    "top_mutual_funds_gb", "top_mutual_funds_hk", "top_mutual_funds_in", "top_mutual_funds_it",
                    "top_mutual_funds_nz", "top_mutual_funds_sg", "top_mutual_funds_us", "top_options_implied_volatality",
                    "top_options_open_interest", "trucking", "undervalued_growth_stocks", "undervalued_large_caps",
                    "waste_management"
                ],
                "equity_fields" = {
                    "exchange": ["stock exchange", "trading venue"],
                    "industry": ["business category", "sector group"],
                    "peer_group": ["peer group", "comparison group", "industry peer"],
                    "region": ["country", "geography", "market region"],
                    "sector": ["market sector", "industry sector"],

                    "eodprice": ["closing price", "end of day price", "eod price"],
                    "fiftytwowkpercentchange": ["52-week change", "yearly percent change"],
                    "intradaymarketcap": ["market cap (intraday)", "realtime market cap"],
                    "intradayprice": ["live price", "real-time price"],
                    "intradaypricechange": ["price change (today)", "daily change", "change %"],

                    "lastclose52weekhigh.lasttwelvemonths": ["52-week high", "year high"],
                    "lastclose52weeklow.lasttwelvemonths": ["52-week low", "year low"],
                    "lastclosemarketcap.lasttwelvemonths": ["market cap (close)", "company value"],
                    "percentchange": ["percent change", "return", "% change"],
                    "avgdailyvol3m": ["average volume", "3-month volume average"],
                    "beta": ["beta", "volatility"],
                    "dayvolume": ["today's volume", "traded volume"],
                    "eodvolume": ["end of day volume", "daily volume"],

                    "pctheldinsider": ["insider ownership", "held by insiders"],
                    "pctheldinst": ["institutional ownership", "held by institutions"],
                    "days_to_cover_short.value": ["days to cover", "short interest ratio"],
                    "short_interest.value": ["short interest", "total shares short"],
                    "short_interest_percentage_change.value": ["short interest change %"],
                    "short_percentage_of_float.value": ["% of float short", "short % float"],
                    "short_percentage_of_shares_outstanding.value": ["% of shares short", "short % outstanding"],

                    "bookvalueshare.lasttwelvemonths": ["book value per share", "bvps"],
                    "lastclosemarketcaptotalrevenue.lasttwelvemonths": ["market cap / revenue", "price/sales"],
                    "lastclosepriceearnings.lasttwelvemonths": ["p/e ratio", "price to earnings", "pe ratio"],
                    "lastclosepricetangiblebookvalue.lasttwelvemonths": ["price/tangible book value", "ptbv"],
                    "lastclosetevtotalrevenue.lasttwelvemonths": ["ev/revenue", "enterprise value to revenue"],
                    "pegratio_5y": ["peg ratio", "p/e growth ratio"],
                    "peratio.lasttwelvemonths": ["trailing p/e", "pe ratio"],
                    "pricebookratio.quarterly": ["price/book", "p/b ratio"],

                    "consecutive_years_of_dividend_growth_count": ["dividend growth streak", "years of dividend increases"],
                    "forward_dividend_per_share": ["forward dividend", "expected dividend"],
                    "forward_dividend_yield": ["forward yield", "estimated dividend yield"],

                    "returnonassets.lasttwelvemonths": ["return on assets", "roa"],
                    "returnonequity.lasttwelvemonths": ["return on equity", "roe"],
                    "returnontotalcapital.lasttwelvemonths": ["return on capital", "rotc"],
                    "ebitdainterestexpense.lasttwelvemonths": ["ebitda / interest", "interest coverage (ebitda)"],
                    "ebitinterestexpense.lasttwelvemonths": ["ebit / interest", "interest coverage (ebit)"],
                    "lastclosetevebit.lasttwelvemonths": ["ev/ebit", "enterprise value / ebit"],
                    "lastclosetevebitda.lasttwelvemonths": ["ev/ebitda", "enterprise value / ebitda"],

                    "ltdebtequity.lasttwelvemonths": ["long-term debt/equity", "lt debt to equity"],
                    "netdebtebitda.lasttwelvemonths": ["net debt/ebitda", "leverage ratio"],
                    "totaldebtebitda.lasttwelvemonths": ["total debt/ebitda"],
                    "totaldebtequity.lasttwelvemonths": ["debt to equity", "debt/equity"],

                    "altmanzscoreusingtheaveragestockinformationforaperiod.lasttwelvemonths": ["altman z-score", "bankruptcy score"],
                    "currentratio.lasttwelvemonths": ["current ratio", "liquidity ratio"],
                    "operatingcashflowtocurrentliabilities.lasttwelvemonths": ["ocf to liabilities", "cash flow coverage"],
                    "quickratio.lasttwelvemonths": ["quick ratio", "acid test ratio"],

                    "basicepscontinuingoperations.lasttwelvemonths": ["basic eps", "earnings per share (basic)"],
                    "dilutedeps1yrgrowth.lasttwelvemonths": ["eps growth", "diluted eps growth"],
                    "dilutedepscontinuingoperations.lasttwelvemonths": ["diluted eps", "eps continuing ops"],

                    "ebit.lasttwelvemonths": ["ebit", "earnings before interest & tax"],
                    "ebitda.lasttwelvemonths": ["ebitda", "earnings before interest, tax, depreciation, amortization"],
                    "ebitda1yrgrowth.lasttwelvemonths": ["ebitda growth", "ebitda 1y change"],
                    "ebitdamargin.lasttwelvemonths": ["ebitda margin", "ebitda % margin"],

                    "epsgrowth.lasttwelvemonths": ["eps growth", "earnings growth"],
                    "grossprofit.lasttwelvemonths": ["gross profit"],
                    "grossprofitmargin.lasttwelvemonths": ["gross margin", "gross profit margin"],
                    "netepsbasic.lasttwelvemonthsnetepsdiluted.lasttwelvemonths": ["net eps", "basic and diluted eps"],

                    "netincome1yrgrowth.lasttwelvemonths": ["net income growth", "profit growth"],
                    "netincomeis.lasttwelvemonths": ["net income", "bottom line"],
                    "netincomemargin.lasttwelvemonths": ["net margin", "net profit margin"],
                    "operatingincome.lasttwelvemonths": ["operating income", "operating profit"],

                    "quarterlyrevenuegrowth.quarterly": ["revenue growth", "sales growth"],
                    "totalrevenues.lasttwelvemonths": ["total revenue", "sales"],
                    "totalrevenues1yrgrowth.lasttwelvemonths": ["revenue growth 1y", "sales growth 1y"],

                    "totalassets.lasttwelvemonths": ["total assets"],
                    "totalcashandshortterminvestments.lasttwelvemonths": ["cash and equivalents", "cash reserves"],
                    "totalcommonequity.lasttwelvemonths": ["common equity"],
                    "totalcommonsharesoutstanding.lasttwelvemonths": ["shares outstanding", "common shares"],
                    "totalcurrentassets.lasttwelvemonths": ["current assets"],
                    "totalcurrentliabilities.lasttwelvemonths": ["current liabilities"],
                    "totaldebt.lasttwelvemonths": ["total debt"],
                    "totalequity.lasttwelvemonths": ["total equity", "shareholder equity"],
                    "totalsharesoutstanding": ["total shares", "shares issued"],

                    "capitalexpenditure.lasttwelvemonths": ["capex", "capital expenditures"],
                    "cashfromoperations.lasttwelvemonths": ["operating cash flow"],
                    "cashfromoperations1yrgrowth.lasttwelvemonths": ["cash flow growth"],
                    "leveredfreecashflow.lasttwelvemonths": ["levered FCF", "free cash flow (levered)"],
                    "leveredfreecashflow1yrgrowth.lasttwelvemonths": ["levered FCF growth"],
                    "unleveredfreecashflow.lasttwelvemonths": ["unlevered FCF", "free cash flow (unlevered)"],

                    "environmental_score": ["environmental score", "esg - environmental"],
                    "esg_score": ["esg score", "environmental social governance"],
                    "governance_score": ["governance score", "esg - governance"],
                    "highest_controversy": ["controversy level", "controversy rating"],
                    "social_score": ["social score", "esg - social"]
                },
                "equity_field_values": {
                    "region": [
                        "ar", "at", "au", "be", "br", "ca", "ch", "cl", "cn", "co", "cz", "de", "dk", "ee", "eg", "es", "fi", "fr", "gb",
                        "gr", "hk", "hu", "id", "ie", "il", "in", "is", "it", "jp", "kr", "kw", "lk", "lt", "lv", "mx", "my", "nl", "no",
                        "nz", "pe", "ph", "pk", "pl", "pt", "qa", "ro", "ru", "sa", "se", "sg", "sr", "sw", "th", "tr", "tw", "us", "ve",
                        "vn", "za"
                    ],
                    "exchange": {
                        "ar": ["BUE"], "at": ["VIE"], "au": ["ASX"], "be": ["BRU"], "br": ["SAO"],
                        "ca": ["CNQ", "NEO", "TOR", "VAN"], "ch": ["EBS"], "cl": ["SGO"], "cn": ["SHH", "SHZ"], "co": ["BVC"],
                        "cz": ["PRA"], "de": ["BER", "DUS", "FRA", "GER", "HAM", "MUN", "STU"], "dk": ["CPH"], "ee": ["TAL"], "eg": ["CAI"],
                        "es": ["MCE"], "fi": ["HEL"], "fr": ["PAR"], "gb": ["AQS", "IOB", "LSE"], "gr": ["ATH"],
                        "hk": ["HKG"], "hu": ["BUD"], "id": ["JKT"], "ie": ["ISE"], "il": ["TLV"],
                        "in": ["BSE", "NSI"], "is": ["ICE"], "it": ["MIL"], "jp": ["FKA", "JPX", "SAP"], "kr": ["KOE", "KSC"],
                        "kw": ["KUW"], "lk": [], "lt": ["LIT"], "lv": ["RIS"], "mx": ["MEX"],
                        "my": ["KLS"], "nl": ["AMS"], "no": ["OSL"], "nz": ["NZE"], "pe": [],
                        "ph": ["PHP", "PHS"], "pk": [], "pl": ["WSE"], "pt": ["LIS"], "qa": ["DOH"],
                        "ro": ["BVB"], "ru": [], "sa": ["SAU"], "se": ["STO"], "sg": ["SES"],
                        "sr": [], "sw": ["EBS"], "th": ["SET"], "tr": ["IST"], "tw": ["TAI", "TWO"],
                        "us": ["ASE", "BTS", "CXI", "NCM", "NGM", "NMS", "NYQ", "OEM", "OQB", "OQX", "PCX", "PNK", "YHD"], "ve": ["CCS"],
                        "vn": [], "za": ["JNB"]
                    },
                    "sector": [
                        "Basic Materials", "Communication Services", "Consumer Cyclical", "Consumer Defensive", "Energy", "Financial Services",
                        "Healthcare", "Industrials", "Real Estate", "Technology", "Utilities"
                    ],
                    "industry": {
                        "Basic Materials": [
                            "Agricultural Inputs", "Aluminum", "Building Materials", "Chemicals", "Coking Coal", "Copper", "Gold",
                            "Lumber & Wood Production", "Other Industrial Metals & Mining", "Other Precious Metals & Mining",
                            "Paper & Paper Products", "Silver", "Specialty Chemicals", "Steel"
                        ],
                        "Communication Services": [
                            "Advertising Agencies", "Broadcasting", "Electronic Gaming & Multimedia", "Entertainment",
                            "Internet Content & Information", "Publishing", "Telecom Services"
                        ],
                        "Consumer Cyclical": [
                            "Apparel Manufacturing", "Apparel Retail", "Auto & Truck Dealerships", "Auto Manufacturers", "Auto Parts",
                            "Department Stores", "Footwear & Accessories", "Furnishings, Fixtures & Appliances", "Gambling",
                            "Home Improvement Retail", "Internet Retail", "Leisure", "Lodging", "Luxury Goods", "Packaging & Containers",
                            "Personal Services", "Recreational Vehicles", "Residential Construction", "Resorts & Casinos", "Restaurants",
                            "Specialty Retail", "Textile Manufacturing", "Travel Services"
                        ],
                        "Consumer Defensive": [
                            "Beverages - Brewers", "Beverages - Non-Alcoholic", "Beverages - Wineries & Distilleries", "Confectioners",
                            "Discount Stores", "Education & Training Services", "Farm Products", "Food Distribution", "Grocery Stores",
                            "Household & Personal Products", "Packaged Foods", "Tobacco"
                        ],
                        "Energy": [
                            "Oil Gas Drilling", "Oil Gas E P", "Oil Gas Equipment Services", "Oil Gas Integrated", "Oil Gas Midstream",
                            "Oil Gas Refining Marketing", "Thermal Coal", "Uranium"
                        ],
                        "Financial Services": [
                            "Asset Management", "Banks Diversified", "Banks Regional", "Capital Markets", "Credit Services",
                            "Financial Conglomerates", "Financial Data Stock Exchanges", "Insurance Brokers", "Insurance Diversified",
                            "Insurance Life", "Insurance Property Casualty", "Insurance Reinsurance", "Insurance Specialty",
                            "Mortgage Finance", "Shell Companies"
                        ],
                        "Healthcare": [
                            "Biotechnology", "Diagnostics Research", "Drug Manufacturers General", "Drug Manufacturers Specialty Generic",
                            "Health Information Services", "Healthcare Plans", "Medical Care Facilities", "Medical Devices",
                            "Medical Distribution", "Medical Instruments Supplies", "Pharmaceutical Retailers"
                        ],
                        "Industrials": [
                            "Aerospace Defense", "Airlines", "Airports Air Services", "Building Products Equipment",
                            "Business Equipment Supplies", "Conglomerates", "Consulting Services", "Electrical Equipment Parts",
                            "Engineering Construction", "Farm Heavy Construction Machinery", "Industrial Distribution",
                            "Infrastructure Operations", "Integrated Freight Logistics", "Marine Shipping", "Metal Fabrication",
                            "Pollution Treatment Controls", "Railroads", "Rental Leasing Services", "Security Protection Services",
                            "Specialty Business Services", "Specialty Industrial Machinery", "Staffing Employment Services",
                            "Tools Accessories", "Trucking", "Waste Management"
                        ],
                        "Real Estate": [
                            "Real Estate Development", "Real Estate Diversified", "Real Estate Services", "Reit Diversified",
                            "Reit Healthcare Facilities", "Reit Hotel Motel", "Reit Industrial", "Reit Mortgage", "Reit Office",
                            "Reit Residential", "Reit Retail", "Reit Specialty"
                        ],
                        "Technology": [
                            "Communication Equipment", "Computer Hardware", "Consumer Electronics", "Electronic Components",
                            "Electronics Computer Distribution", "Information Technology Services", "Scientific Technical Instruments",
                            "Semiconductor Equipment Materials", "Semiconductors", "Software Application", "Software Infrastructure",
                            "Solar"
                        ],
                        "Utilities": [
                            "Utilities Diversified", "Utilities Independent Power Producers", "Utilities Regulated Electric",
                            "Utilities Regulated Gas", "Utilities Regulated Water", "Utilities Renewable"
                        ]
                    },
                    "peer_group": [
                        "Aerospace & Defense", "Auto Components", "Automobiles", "Banks", "Building Products", "Chemicals",
                        "China Fund Aggressive Allocation Fund", "China Fund Equity Funds", "China Fund QDII Greater China Equity",
                        "China Fund QDII Sector Equity", "China Fund Sector Equity Financial and Real Estate", "Commercial Services",
                        "Construction & Engineering", "Construction Materials", "Consumer Durables", "Consumer Services",
                        "Containers & Packaging", "Diversified Financials", "Diversified Metals", "EAA CE Global Large-Cap Blend Equity",
                        "EAA CE Other", "EAA CE Sector Equity Biotechnology", "EAA CE UK Large-Cap Equity", "EAA CE UK Small-Cap Equity",
                        "EAA Fund Asia ex-Japan Equity", "EAA Fund China Equity", "EAA Fund China Equity - A Shares",
                        "EAA Fund Denmark Equity", "EAA Fund EUR Aggressive Allocation - Global", "EAA Fund EUR Corporate Bond",
                        "EAA Fund EUR Moderate Allocation - Global", "EAA Fund Emerging Europe ex-Russia Equity",
                        "EAA Fund Europe Large-Cap Blend Equity", "EAA Fund Eurozone Large-Cap Equity", "EAA Fund Germany Equity",
                        "EAA Fund Global Emerging Markets Equity", "EAA Fund Global Equity Income", "EAA Fund Global Flex-Cap Equity",
                        "EAA Fund Global Large-Cap Blend Equity", "EAA Fund Global Large-Cap Growth Equity", "EAA Fund Hong Kong Equity",
                        "EAA Fund Japan Large-Cap Equity", "EAA Fund Other Bond", "EAA Fund Other Equity", "EAA Fund RMB Bond - Onshore",
                        "EAA Fund Sector Equity Consumer Goods & Services", "EAA Fund Sector Equity Financial Services",
                        "EAA Fund Sector Equity Industrial Materials", "EAA Fund Sector Equity Technology",
                        "EAA Fund South Africa & Namibia Equity", "EAA Fund Switzerland Equity", "EAA Fund US Large-Cap Blend Equity",
                        "EAA Fund USD Corporate Bond", "Electrical Equipment", "Energy Services", "Food Products", "Food Retailers",
                        "Healthcare", "Homebuilders", "Household Products", "India CE Multi-Cap", "India Fund Large-Cap",
                        "India Fund Sector - Financial Services", "Industrial Conglomerates", "Insurance", "Machinery", "Media",
                        "Mexico Fund Mexico Equity", "Oil & Gas Producers", "Paper & Forestry", "Pharmaceuticals", "Precious Metals",
                        "Real Estate", "Refiners & Pipelines", "Retailing", "Semiconductors", "Software & Services", "Steel",
                        "Technology Hardware", "Telecommunication Services", "Textiles & Apparel", "Traders & Distributors",
                        "Transportation", "Transportation Infrastructure", "US CE Convertibles", "US CE Options-based",
                        "US CE Preferred Stock", "US Fund China Region", "US Fund Consumer Cyclical",
                        "US Fund Diversified Emerging Mkts", "US Fund Equity Energy", "US Fund Equity Precious Metals",
                        "US Fund Financial", "US Fund Foreign Large Blend", "US Fund Health", "US Fund Large Blend",
                        "US Fund Large Growth", "US Fund Large Value", "US Fund Miscellaneous Region", "US Fund Natural Resources",
                        "US Fund Technology", "US Fund Trading–Leveraged Equity", "Utilities"
                    ]
                }
                "fund_fields" = {
                    "annualreturnnavy1categoryrank": ["1-year return rank", "category rank (1Y)", "annual return rank"],
                    "categoryname": ["fund category", "investment category", "category name"],
                    "exchange": ["stock exchange", "fund exchange", "trading platform"],
                    "initialinvestment": ["minimum investment", "initial buy-in", "first investment amount"],
                    "performanceratingoverall": ["overall performance rating", "rating", "fund rating", "morningstar rating"],
                    "riskratingoverall": ["risk rating", "risk level", "overall risk score"],
                    "eodprice": ["closing price", "end of day price", "eod price"],
                    "intradayprice": ["current price", "real-time price", "intraday value"],
                    "intradaypricechange": ["price change today", "daily change", "change in price"]
                },
                "fund_field_values": {
                "exchange": ["NAS"]
                "categoryname": ["Foreign Large Value", "Foreign Large Blend", "Foreign Large Growth", "Foreign Small/Mid Growth", 
                    "Foreign Small/Mid Blend", "Foreign Small/Mid Value", "High Yield Bond", "Large Blend", "Large Growth", 
                    "Mid-Cap Growth"]
                }
                "operators": {
                    "gt": ["greater than", "more than", "above", "over", "at least", ">"],
                    "lt": ["less than", "smaller than", "below", "under", "up to", "<"],
                    "eq": ["equal to", "is", "in the"],
                    "is-in": ["is one of", "has a rating of"],
                    "btwn": ["between"]
                },
                "country_code_mapping" = {
                    "ar": "Argentina", "at": "Austria", "au": "Australia", "be": "Belgium", "br": "Brazil",
                    "ca": "Canada", "ch": "Switzerland", "cl": "Chile", "cn": "China", "co": "Colombia",
                    "cz": "Czech Republic", "de": "Germany", "dk": "Denmark", "ee": "Estonia", "eg": "Egypt",
                    "es": "Spain", "fi": "Finland", "fr": "France", "gb": "United Kingdom", "gr": "Greece",
                    "hk": "Hong Kong", "hu": "Hungary", "id": "Indonesia", "ie": "Ireland", "il": "Israel",
                    "in": "India", "is": "Iceland", "it": "Italy", "jp": "Japan", "kr": "South Korea",
                    "kw": "Kuwait", "lk": "Sri Lanka", "lt": "Lithuania", "lv": "Latvia", "mx": "Mexico",
                    "my": "Malaysia", "nl": "Netherlands", "no": "Norway", "nz": "New Zealand", "pe": "Peru",
                    "ph": "Philippines", "pk": "Pakistan", "pl": "Poland", "pt": "Portugal", "qa": "Qatar",
                    "ro": "Romania", "ru": "Russia", "sa": "Saudi Arabia", "se": "Sweden", "sg": "Singapore",
                    "sr": "Suriname", "th": "Thailand", "tr": "Turkey", "tw": "Taiwan", "us": "United States",
                    "ve": "Venezuela", "vn": "Vietnam", "za": "South Africa"
                },
            "mapping_guidelines": {
                "description": "When extracting 'included_sectors' or 'excluded_sectors', use these rules to map informal terms to canonical IDs.",
                "examples": {
                    "basic-materials": ["basic materials", "chemicals", "steel", "gold"],
                    "communication-services": ["telecom", "media", "entertainment"],
                    "consumer-cyclical": ["retail", "autos", "restaurants"],
                    "consumer-defensive": ["grocery", "packaged foods"],
                    "energy": ["oil & gas", "renewable energy"],
                    "financial-services": ["banks", "insurance"],
                    "healthcare": ["pharma", "biotech", "medical devices"],
                    "industrials": ["aerospace", "manufacturing"],
                    "real-estate": ["real estate", "reit"],
                    "technology": ["tech", "software", "semiconductors", "hardware"],
                    "utilities": ["utilities", "power"]
                }
            },
            "entity_handling": {
                "description": "When extracting company names or tickers, use these rules.",
                "rules": [
                    "Extract only verbatim instrument names or tickers.",
                    "Do not infer or substitute entities.",
                    "If a user says 'Tesla stock', the extracted entity is 'Tesla'.",
                    "If a user says 'Apple shares', the extracted entity is 'Apple'."
                ]
            },
            "predefined_screener_with_value_examples": [
                {'field': 'advertising_agencies', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Communication Services']}, {'operator': 'EQ', 'operands': ['industry', 'Advertising Agencies']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'aggressive_small_caps', 'query': {'operator': 'and', 'operands': [{'operator': 'gt', 'operands': ['epsgrowth.lasttwelvemonths', 25.0]}, {'operator': 'lt', 'operands': ['intradaymarketcap', 2000000000]}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'all_cryptocurrencies_us', 'query': {'operator': 'and', 'operands': [{'operator': 'eq', 'operands': ['currency', 'USD']}, {'operator': 'eq', 'operands': ['exchange', 'CCC']}]}},
                {'field': 'aluminum', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Basic Materials']}, {'operator': 'EQ', 'operands': ['industry', 'Aluminum']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'asset_management', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Financial Services']}, {'operator': 'EQ', 'operands': ['industry', 'Asset Management']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'auto_parts', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Consumer Cyclical']}, {'operator': 'EQ', 'operands': ['industry', 'Auto Parts']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'beverages_brewers', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Consumer Defensive']}, {'operator': 'EQ', 'operands': ['industry', 'Beverages—Brewers']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'biotechnology', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Healthcare']}, {'operator': 'EQ', 'operands': ['industry', 'Biotechnology']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'communication_equipment', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Technology']}, {'operator': 'EQ', 'operands': ['industry', 'Communication Equipment']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'confectioners', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Consumer Defensive']}, {'operator': 'EQ', 'operands': ['industry', 'Confectioners']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'conglomerates', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Industrials']}, {'operator': 'EQ', 'operands': ['industry', 'Conglomerates']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'conservative_foreign_funds', 'query': {'operator': 'and', 'operands': [{'operator': 'or', 'operands': [{'operator': 'EQ', 'operands': ['categoryname', 'Foreign Large Value']}, {'operator': 'EQ', 'operands': ['categoryname', 'Foreign Large Blend']}, {'operator': 'EQ', 'operands': ['categoryname', 'Foreign Large Growth']}, {'operator': 'EQ', 'operands': ['categoryname', 'Foreign Small/Mid Growth']}, {'operator': 'EQ', 'operands': ['categoryname', 'Foreign Large Blend']}, {'operator': 'EQ', 'operands': ['categoryname', 'Foreign Small/Mid Blend']}, {'operator': 'EQ', 'operands': ['categoryname', 'Foreign Small/Mid Value']}, {'operator': 'EQ', 'operands': ['categoryname', 'Foreign Small/Mid Blend']}, {'operator': 'EQ', 'operands': ['categoryname', 'Foreign Small/Mid Value']}, {'operator': 'EQ', 'operands': ['categoryname', 'Foreign Small/Mid Blend']}, {'operator': 'EQ', 'operands': ['categoryname', 'Foreign Small/Mid Value']}, {'operator': 'EQ', 'operands': ['categoryname', 'Foreign Small/Mid Blend']}, {'operator': 'EQ', 'operands': ['categoryname', 'Foreign Small/Mid Value']}]}, {'operator': 'or', 'operands': [{'operator': 'EQ', 'operands': ['performanceratingoverall', 4]}, {'operator': 'EQ', 'operands': ['performanceratingoverall', 5]}]}, {'operator': 'lt', 'operands': ['initialinvestment', 100001]}, {'operator': 'lt', 'operands': ['annualreturnnavy1categoryrank', 50]}, {'operator': 'or', 'operands': [{'operator': 'EQ', 'operands': ['riskratingoverall', 1]}, {'operator': 'EQ', 'operands': ['riskratingoverall', 3]}, {'operator': 'EQ', 'operands': ['riskratingoverall', 2]}]}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NAS']}]}]}},
                {'field': 'copper', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Basic Materials']}, {'operator': 'EQ', 'operands': ['industry', 'Copper']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'credit_services', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Financial Services']}, {'operator': 'EQ', 'operands': ['industry', 'Credit Services']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'day_gainers', 'query': {'operator': 'AND', 'operands': [{'operator': 'GT', 'operands': ['percentchange', 3.0]}, {'operator': 'eq', 'operands': ['region', 'us']}, {'operator': 'or', 'operands': [{'operator': 'BTWN', 'operands': ['intradaymarketcap', 2000000000, 10000000000]}, {'operator': 'BTWN', 'operands': ['intradaymarketcap', 10000000000, 100000000000]}, {'operator': 'GT', 'operands': ['intradaymarketcap', 100000000000]}]}, {'operator': 'gte', 'operands': ['intradayprice', 5]}, {'operator': 'gt', 'operands': ['dayvolume', 15000]}, {'operator': 'must_not', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'PNK']}, {'operator': 'eq', 'operands': ['exchange', 'OQB']}, {'operator': 'eq', 'operands': ['exchange', 'OQX']}, {'operator': 'eq', 'operands': ['exchange', 'OEM']}, {'operator': 'eq', 'operands': ['exchange', 'OGM']}, {'operator': 'eq', 'operands': ['exchange', 'XXX']}, {'operator': 'eq', 'operands': ['exchange', 'OBB']}]}]}},
                {'field': 'day_gainers_americas', 'query': {'operator': 'AND', 'operands': [{'operator': 'GT', 'operands': ['percentchange', 3.0]}, {'operator': 'OR', 'operands': [{'operator': 'eq', 'operands': ['region', 'ca']}, {'operator': 'eq', 'operands': ['region', 'mx']}, {'operator': 'eq', 'operands': ['region', 'us']}, {'operator': 'eq', 'operands': ['region', 'ar']}, {'operator': 'eq', 'operands': ['region', 'br']}, {'operator': 'eq', 'operands': ['region', 'cl']}, {'operator': 'eq', 'operands': ['region', 'pe']}, {'operator': 'eq', 'operands': ['region', 'sr']}, {'operator': 'eq', 'operands': ['region', 've']}]}, {'operator': 'or', 'operands': [{'operator': 'BTWN', 'operands': ['intradaymarketcap', 2000000000, 10000000000]}, {'operator': 'BTWN', 'operands': ['intradaymarketcap', 10000000000, 100000000000]}, {'operator': 'GT', 'operands': ['intradaymarketcap', 100000000000]}]}, {'operator': 'gt', 'operands': ['dayvolume', 15000]}]}},
                {'field': 'day_gainers_asia', 'query': {'operator': 'AND', 'operands': [{'operator': 'GT', 'operands': ['percentchange', 3.0]}, {'operator': 'OR', 'operands': [{'operator': 'eq', 'operands': ['region', 'cn']}, {'operator': 'eq', 'operands': ['region', 'hk']}, {'operator': 'eq', 'operands': ['region', 'id']}, {'operator': 'eq', 'operands': ['region', 'in']}, {'operator': 'eq', 'operands': ['region', 'jp']}, {'operator': 'eq', 'operands': ['region', 'kr']}, {'operator': 'eq', 'operands': ['region', 'my']}, {'operator': 'eq', 'operands': ['region', 'ph']}, {'operator': 'eq', 'operands': ['region', 'pk']}, {'operator': 'eq', 'operands': ['region', 'sg']}, {'operator': 'eq', 'operands': ['region', 'tw']}, {'operator': 'eq', 'operands': ['region', 'th']}, {'operator': 'eq', 'operands': ['region', 'vn']}]}, {'operator': 'or', 'operands': [{'operator': 'BTWN', 'operands': ['intradaymarketcap', 2000000000, 10000000000]}, {'operator': 'BTWN', 'operands': ['intradaymarketcap', 10000000000, 100000000000]}, {'operator': 'GT', 'operands': ['intradaymarketcap', 100000000000]}]}, {'operator': 'gt', 'operands': ['dayvolume', 15000]}]}},
                {'field': 'day_gainers_au', 'query': {'operator': 'and', 'operands': [{'operator': 'gt', 'operands': ['percentchange', 2.5]}, {'operator': 'eq', 'operands': ['region', 'au']}]}},
                {'field': 'day_losers_europe', 'query': {'operator': 'AND', 'operands': [{'operator': 'LT', 'operands': ['percentchange', -2.5]}, {'operator': 'OR', 'operands': [{'operator': 'eq', 'operands': ['region', 'at']}, {'operator': 'eq', 'operands': ['region', 'be']}, {'operator': 'eq', 'operands': ['region', 'ch']}, {'operator': 'eq', 'operands': ['region', 'cz']}, {'operator': 'eq', 'operands': ['region', 'de']}, {'operator': 'eq', 'operands': ['region', 'dk']}, {'operator': 'eq', 'operands': ['region', 'es']}, {'operator': 'eq', 'operands': ['region', 'fi']}, {'operator': 'eq', 'operands': ['region', 'fr']}, {'operator': 'eq', 'operands': ['region', 'gb']}, {'operator': 'eq', 'operands': ['region', 'gr']}, {'operator': 'eq', 'operands': ['region', 'hu']}, {'operator': 'eq', 'operands': ['region', 'ie']}, {'operator': 'eq', 'operands': ['region', 'it']}, {'operator': 'eq', 'operands': ['region', 'nl']}, {'operator': 'eq', 'operands': ['region', 'no']}, {'operator': 'eq', 'operands': ['region', 'pl']}, {'operator': 'eq', 'operands': ['region', 'pt']}, {'operator': 'eq', 'operands': ['region', 'ru']}, {'operator': 'eq', 'operands': ['region', 'se']}, {'operator': 'eq', 'operands': ['region', 'tr']}]}, {'operator': 'or', 'operands': [{'operator': 'BTWN', 'operands': ['intradaymarketcap', 2000000000, 10000000000]}, {'operator': 'BTWN', 'operands': ['intradaymarketcap', 10000000000, 100000000000]}, {'operator': 'GT', 'operands': ['intradaymarketcap', 100000000000]}]}, {'operator': 'gt', 'operands': ['dayvolume', 20000]}]}},
                {'field': 'department_stores', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Consumer Cyclical']}, {'operator': 'EQ', 'operands': ['industry', 'Department Stores']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'education_training_services', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Consumer Defensive']}, {'operator': 'EQ', 'operands': ['industry', 'Education & Training Services']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'farm_products', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Consumer Defensive']}, {'operator': 'EQ', 'operands': ['industry', 'Farm Products']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'gold', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Basic Materials']}, {'operator': 'EQ', 'operands': ['industry', 'Gold']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'grocery_stores', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Consumer Defensive']}, {'operator': 'EQ', 'operands': ['industry', 'Grocery Stores']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'growth_technology_stocks', 'query': {'operator': 'and', 'operands': [{'operator': 'or', 'operands': [{'operator': 'BTWN', 'operands': ['quarterlyrevenuegrowth.quarterly', 25, 50]}, {'operator': 'BTWN', 'operands': ['quarterlyrevenuegrowth.quarterly', 50, 100]}, {'operator': 'GT', 'operands': ['quarterlyrevenuegrowth.quarterly', 100]}]}, {'operator': 'or', 'operands': [{'operator': 'BTWN', 'operands': ['epsgrowth.lasttwelvemonths', 25, 50]}, {'operator': 'BTWN', 'operands': ['epsgrowth.lasttwelvemonths', 50, 100]}, {'operator': 'GT', 'operands': ['epsgrowth.lasttwelvemonths', 100]}]}, {'operator': 'eq', 'operands': ['sector', 'Technology']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'high_yield_bond', 'query': {'operator': 'and', 'operands': [{'operator': 'or', 'operands': [{'operator': 'EQ', 'operands': ['performanceratingoverall', 4]}, {'operator': 'EQ', 'operands': ['performanceratingoverall', 5]}]}, {'operator': 'lt', 'operands': ['initialinvestment', 100001]}, {'operator': 'lt', 'operands': ['annualreturnnavy1categoryrank', 50]}, {'operator': 'or', 'operands': [{'operator': 'EQ', 'operands': ['riskratingoverall', 1]}, {'operator': 'EQ', 'operands': ['riskratingoverall', 3]}, {'operator': 'EQ', 'operands': ['riskratingoverall', 2]}]}, {'operator': 'or', 'operands': [{'operator': 'EQ', 'operands': ['categoryname', 'High Yield Bond']}]}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NAS']}]}]}},
                {'field': 'information_technology_services', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Technology']}, {'operator': 'EQ', 'operands': ['industry', 'Information Technology Services']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'insurance_brokers', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Financial Services']}, {'operator': 'EQ', 'operands': ['industry', 'Insurance Brokers']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'lodging', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Consumer Cyclical']}, {'operator': 'EQ', 'operands': ['industry', 'Lodging']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'lumber_wood_production', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Basic Materials']}, {'operator': 'EQ', 'operands': ['industry', 'Lumber & Wood Production']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'medical_instruments_supplies', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Healthcare']}, {'operator': 'EQ', 'operands': ['industry', 'Medical Instruments & Supplies']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'mega_cap_hc', 'query': {'operator': 'AND', 'operands': [{'operator': 'or', 'operands': [{'operator': 'EQ', 'operands': ['region', 'us']}]}, {'operator': 'or', 'operands': [{'operator': 'BTWN', 'operands': ['intradaymarketcap', 10000000000, 100000000000]}]}, {'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'or', 'operands': [{'operator': 'EQ', 'operands': ['sector', 'Healthcare']}]}]}},
                {'field': 'metal_fabrication', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Industrials']}, {'operator': 'EQ', 'operands': ['industry', 'Metal Fabrication']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'most_actives', 'query': {'operator': 'AND', 'operands': [{'operator': 'eq', 'operands': ['region', 'us']}, {'operator': 'or', 'operands': [{'operator': 'BTWN', 'operands': ['intradaymarketcap', 2000000000, 10000000000]}, {'operator': 'BTWN', 'operands': ['intradaymarketcap', 10000000000, 100000000000]}, {'operator': 'GT', 'operands': ['intradaymarketcap', 100000000000]}]}, {'operator': 'gt', 'operands': ['dayvolume', 5000000]}, {'operator': 'must_not', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'PNK']}, {'operator': 'eq', 'operands': ['exchange', 'OQB']}, {'operator': 'eq', 'operands': ['exchange', 'OQX']}, {'operator': 'eq', 'operands': ['exchange', 'OEM']}, {'operator': 'eq', 'operands': ['exchange', 'OGM']}, {'operator': 'eq', 'operands': ['exchange', 'XXX']}, {'operator': 'eq', 'operands': ['exchange', 'OBB']}]}]}},
                {'field': 'most_actives_americas', 'query': {'operator': 'AND', 'operands': [{'operator': 'OR', 'operands': [{'operator': 'eq', 'operands': ['region', 'ca']}, {'operator': 'eq', 'operands': ['region', 'mx']}, {'operator': 'eq', 'operands': ['region', 'us']}, {'operator': 'eq', 'operands': ['region', 'ar']}, {'operator': 'eq', 'operands': ['region', 'br']}, {'operator': 'eq', 'operands': ['region', 'cl']}, {'operator': 'eq', 'operands': ['region', 'pe']}, {'operator': 'eq', 'operands': ['region', 'sr']}, {'operator': 'eq', 'operands': ['region', 've']}]}, {'operator': 'or', 'operands': [{'operator': 'BTWN', 'operands': ['intradaymarketcap', 2000000000, 10000000000]}, {'operator': 'BTWN', 'operands': ['intradaymarketcap', 10000000000, 100000000000]}, {'operator': 'GT', 'operands': ['intradaymarketcap', 100000000000]}]}, {'operator': 'gt', 'operands': ['dayvolume', 5000000]}]}},
                {'field': 'most_watched_tickers', 'query': {'operator': 'and', 'operands': [{'operator': 'gt', 'operands': ['portfolioheldcount', 1000]}]}},
                {'field': 'ms_basic_materials', 'query': {'operator': 'and', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'or', 'operands': [{'operator': 'EQ', 'operands': ['sector', 'Basic Materials']}]}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}, {'operator': 'eq', 'operands': ['exchange', 'NAS']}]}]}},
                {'field': 'oil_gas_equipment_services', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Energy']}, {'operator': 'EQ', 'operands': ['industry', 'Oil & Gas Equipment & Services']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'oil_gas_refining_marketing', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Energy']}, {'operator': 'EQ', 'operands': ['industry', 'Oil & Gas Refining & Marketing']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'packaging_containers', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Consumer Cyclical']}, {'operator': 'EQ', 'operands': ['industry', 'Packaging & Containers']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'paper_paper_products', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Basic Materials']}, {'operator': 'EQ', 'operands': ['industry', 'Paper & Paper Products']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'personal_services', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Consumer Cyclical']}, {'operator': 'EQ', 'operands': ['industry', 'Personal Services']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'pollution_treatment_controls', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Industrials']}, {'operator': 'EQ', 'operands': ['industry', 'Pollution & Treatment Controls']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'portfolio_anchors', 'query': {'operator': 'and', 'operands': [{'operator': 'or', 'operands': [{'operator': 'EQ', 'operands': ['categoryname', 'Large Blend']}]}, {'operator': 'or', 'operands': [{'operator': 'EQ', 'operands': ['performanceratingoverall', 4]}, {'operator': 'EQ', 'operands': ['performanceratingoverall', 5]}]}, {'operator': 'lt', 'operands': ['initialinvestment', 100001]}, {'operator': 'lt', 'operands': ['annualreturnnavy1categoryrank', 50]}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NAS']}]}]}},
                {'field': 'railroads', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Industrials']}, {'operator': 'EQ', 'operands': ['industry', 'Railroads']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'real_estate_development', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Real Estate']}, {'operator': 'EQ', 'operands': ['industry', 'Real Estate—Development']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'recreational_vehicles', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Consumer Cyclical']}, {'operator': 'EQ', 'operands': ['industry', 'Recreational Vehicles']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'reit_diversified', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Real Estate']}, {'operator': 'EQ', 'operands': ['industry', 'REIT—Diversified']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'rental_leasing_services', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Industrials']}, {'operator': 'EQ', 'operands': ['industry', 'Rental & Leasing Services']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'residential_construction', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Consumer Cyclical']}, {'operator': 'EQ', 'operands': ['industry', 'Residential Construction']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'resorts_casinos', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Consumer Cyclical']}, {'operator': 'EQ', 'operands': ['industry', 'Resorts & Casinos']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'restaurants', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Consumer Cyclical']}, {'operator': 'EQ', 'operands': ['industry', 'Restaurants']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'scientific_technical_instruments', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Technology']}, {'operator': 'EQ', 'operands': ['industry', 'Scientific & Technical Instruments']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'security_protection_services', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Industrials']}, {'operator': 'EQ', 'operands': ['industry', 'Security & Protection Services']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'semiconductor_equipment_materials', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Technology']}, {'operator': 'EQ', 'operands': ['industry', 'Semiconductor Equipment & Materials']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'silver', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Basic Materials']}, {'operator': 'EQ', 'operands': ['industry', 'Silver']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'small_cap_gainers', 'query': {'operator': 'and', 'operands': [{'operator': 'gt', 'operands': ['percentchange', 5.0]}, {'operator': 'lt', 'operands': ['intradaymarketcap', 2000000000]}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'solid_large_growth_funds', 'query': {'operator': 'and', 'operands': [{'operator': 'or', 'operands': [{'operator': 'EQ', 'operands': ['categoryname', 'Large Growth']}]}, {'operator': 'or', 'operands': [{'operator': 'EQ', 'operands': ['performanceratingoverall', 4]}, {'operator': 'EQ', 'operands': ['performanceratingoverall', 5]}]}, {'operator': 'lt', 'operands': ['initialinvestment', 100001]}, {'operator': 'lt', 'operands': ['annualreturnnavy1categoryrank', 50]}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NAS']}]}]}},
                {'field': 'solid_midcap_growth_funds', 'query': {'operator': 'and', 'operands': [{'operator': 'or', 'operands': [{'operator': 'EQ', 'operands': ['categoryname', 'Mid-Cap Growth']}]}, {'operator': 'or', 'operands': [{'operator': 'EQ', 'operands': ['performanceratingoverall', 4]}, {'operator': 'EQ', 'operands': ['performanceratingoverall', 5]}]}, {'operator': 'lt', 'operands': ['initialinvestment', 100001]}, {'operator': 'lt', 'operands': ['annualreturnnavy1categoryrank', 50]}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NAS']}]}]}},
                {'field': 'specialty_chemicals', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Basic Materials']}, {'operator': 'EQ', 'operands': ['industry', 'Specialty Chemicals']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'top_energy_us', 'query': {'operator': 'and', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'or', 'operands': [{'operator': 'EQ', 'operands': ['sector', 'Energy']}]}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}, {'operator': 'eq', 'operands': ['exchange', 'NAS']}]}]}},
                {'field': 'top_etfs_us', 'query': {'operator': 'and', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 10]}, {'operator': 'or', 'operands': [{'operator': 'EQ', 'operands': ['performanceratingoverall', 5]}, {'operator': 'EQ', 'operands': ['performanceratingoverall', 4]}]}, {'operator': 'or', 'operands': [{'operator': 'EQ', 'operands': ['region', 'us']}]}]}},
                {'field': 'top_mutual_funds', 'query': {'operator': 'and', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 15]}, {'operator': 'or', 'operands': [{'operator': 'EQ', 'operands': ['performanceratingoverall', 4]}, {'operator': 'EQ', 'operands': ['performanceratingoverall', 5]}]}, {'operator': 'gt', 'operands': ['initialinvestment', 1000]}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NAS']}]}]}},
                {'field': 'top_mutual_funds_in', 'query': {'operator': 'and', 'operands': [{'operator': 'or', 'operands': [{'operator': 'EQ', 'operands': ['exchange', 'BSE']}]}]}},
                {'field': 'top_options_implied_volatality', 'query': {'operator': 'and', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'OPR']}, {'operator': 'gt', 'operands': ['implied_volatility', 15]}]}},
                {'field': 'top_options_open_interest', 'query': {'operator': 'and', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'OPR']}, {'operator': 'gt', 'operands': ['open_interest', 10000]}]}},
                {'field': 'trucking', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Industrials']}, {'operator': 'EQ', 'operands': ['industry', 'Trucking']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'undervalued_growth_stocks', 'query': {'operator': 'and', 'operands': [{'operator': 'or', 'operands': [{'operator': 'BTWN', 'operands': ['peratio.lasttwelvemonths', 0, 20]}]}, {'operator': 'or', 'operands': [{'operator': 'LT', 'operands': ['pegratio_5y', 1]}]}, {'operator': 'or', 'operands': [{'operator': 'BTWN', 'operands': ['epsgrowth.lasttwelvemonths', 25, 50]}, {'operator': 'BTWN', 'operands': ['epsgrowth.lasttwelvemonths', 50, 100]}, {'operator': 'GT', 'operands': ['epsgrowth.lasttwelvemonths', 100]}]}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'undervalued_large_caps', 'query': {'operator': 'and', 'operands': [{'operator': 'btwn', 'operands': ['peratio.lasttwelvemonths', 0, 20]}, {'operator': 'lt', 'operands': ['pegratio_5y', 1]}, {'operator': 'btwn', 'operands': ['intradaymarketcap', 10000000000, 100000000000]}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}},
                {'field': 'waste_management', 'query': {'operator': 'AND', 'operands': [{'operator': 'gt', 'operands': ['intradayprice', 5]}, {'operator': 'EQ', 'operands': ['sector', 'Industrials']}, {'operator': 'EQ', 'operands': ['industry', 'Waste Management']}, {'operator': 'or', 'operands': [{'operator': 'eq', 'operands': ['exchange', 'NMS']}, {'operator': 'eq', 'operands': ['exchange', 'NYQ']}]}]}}
            ]
            # Use the above predefined_screener_value_examples to set values for the custom filter fields.
        },
        "examples": [
            {
                "input": "Can you analyze MSFT and tell me about the tech sector?",
                "output": { "tool_name": "specific_stock_analysis", "parameters": { "companies": ["MSFT", "tech"] } }
            },
            {
                "input": "I want to diversify my portfolio. Avoid banks and pharma.",
                "output": { "tool_name": "get_sector_industry_recommendation", "parameters": { "excluded_sectors": ["financial-services", "healthcare"] } }
            },
            {
                "input": "Buy 10 shares of NVDA for 130 dollars.",
                "output": { "tool_name": "add_to_database", "parameters": { "company": "NVDA", "quantity": 10, "price": 130.0 } }
            },
            {
                "input": "Show me all my holdings.",
                "output": { "tool_name": "list_database", "parameters": {} }
            },
            {
                "input": "Thanks, that's all for now.",
                "output": { "tool_name": "no_op", "parameters": { "reason": "User is ending the conversation." } }
            },
            {
                "input": "Show me US technology stocks with a P/E ratio under 25 and revenue growth over 15%.",
                "output": {
                    "tool_name": "screen_stocks",
                    "parameters": {
                        "screener_type": "equity",
                        "comparison_type": "and",
                        "custom_filters": [
                            { "field": "region", "operator": "eq", "value": "us" },
                            { "field": "sector", "operator": "eq", "value": "Technology" },
                            { "field": "peratio.lasttwelvemonths", "operator": "lt", "value": 25 },
                            { "field": "quarterlyrevenuegrowth.quarterly", "operator": "gt", "value": 0.15 }
                        ],
                        "sort_field": "marketCap",
                        "sort_ascending": false
                    }
                }
            },
            {
                "input": "I'm looking for Large Growth funds with a 4 or 5 star rating.",
                "output": {
                    "tool_name": "screen_stocks",
                    "parameters": {
                        "screener_type": "fund",
                        "comparison_type": "and",
                        "custom_filters": [
                            { "field": "categoryname", "operator": "eq", "value": "Large Growth" },
                            { "field": "performanceratingoverall", "operator": "is-in", "value": [4, 5] }
                        ]
                    }
                }
            },
        ]
    }''')
    
    human_message = HumanMessage(content=f'''Generate tool calls according to the guidelines given in the system prompt
        Query: "{user_input}"
    ''')
    
    response = llm_with_tools.invoke([sys_message] + [human_message])

    return {
        "pending_tool_calls": response.tool_calls
    }

