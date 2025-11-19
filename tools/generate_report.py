import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from yahooquery import Ticker
from playwright.sync_api import sync_playwright
from datetime import datetime
import base64
from io import BytesIO
import logging
from currency_converter import CurrencyConverter
from rich.console import Console

logging.getLogger('matplotlib.font_manager').disabled = True
logging.getLogger('yahooquery').setLevel(logging.ERROR)

SUPER_SECTOR_MAP = {
    "basic-materials": [
        "agricultural-inputs", 
        "aluminum", 
        "building-materials", 
        "chemicals", 
        "coking-coal", 
        "copper", 
        "gold", 
        "lumber-wood-production", 
        "other-industrial-metals-mining", 
        "other-precious-metals-mining", 
        "paper-paper-products", 
        "silver", 
        "specialty-chemicals", 
        "steel"
    ],

    "communication-services": [
        "advertising-agencies",
        "broadcasting",
        "electronic-gaming-multimedia",
        "entertainment",
        "internet-content-information",
        "publishing",
        "telecom-services"
    ],

    "consumer-cyclical": [
        "apparel-manufacturing",
        "apparel-retail",
        "auto-manufacturers",
        "auto-parts",
        "auto-truck-dealerships",
        "department-stores",
        "footwear-accessories",
        "furnishings-fixtures-appliances",
        "gambling",
        "home-improvement-retail",
        "internet-retail",
        "leisure",
        "lodging",
        "luxury-goods",
        "packaging-containers",
        "personal-services",
        "recreational-vehicles",
        "residential-construction",
        "resorts-casinos",
        "restaurants",
        "specialty-retail",
        "textile-manufacturing",
        "travel-services"
    ],

    "consumer-defensive": [
        "beverages-brewers",
        "beverages-non-alcoholic",
        "beverages-wineries-distilleries",
        "confectioners",
        "discount-stores",
        "education-training-services",
        "farm-products",
        "food-distribution",
        "grocery-stores",
        "household-personal-products",
        "packaged-foods",
        "tobacco",
    ],

    "energy": [
        "oil-gas-drilling",
        "oil-gas-e-p",
        "oil-gas-equipment-services",
        "oil-gas-integrated",
        "oil-gas-midstream",
        "oil-gas-refining-marketing",
        "thermal-coal",
        "uranium"
    ],

    "financial-services": [
        "asset-management",
        "banks-diversified",
        "banks-regional",
        "capital-markets",
        "credit-services",
        "financial-conglomerates",
        "financial-data-stock-exchanges",
        "insurance-brokers",
        "insurance-diversified",
        "insurance-life",
        "insurance-property-casualty",
        "insurance-reinsurance",
        "insurance-specialty",
        "mortgage-finance",
        "shell-companies"
    ],

    "healthcare": [
        "biotechnology",
        "diagnostics-research",
        "drug-manufacturers-general",
        "drug-manufacturers-specialty-generic",
        "health-information-services",
        "healthcare-plans",
        "medical-care-facilities",
        "medical-devices",
        "medical-distribution",
        "medical-instruments-supplies",
        "pharmaceutical-retailers"
    ],

    "industrials": [
        "aerospace-defense",
        "airlines",
        "airports-air-services",
        "building-products-equipment",
        "business-equipment-supplies",
        "conglomerates",
        "consulting-services",
        "electrical-equipment-parts",
        "engineering-construction",
        "farm-heavy-construction-machinery",
        "industrial-distribution",
        "infrastructure-operations",
        "integrated-freight-logistics",
        "marine-shipping",
        "metal-fabrication",
        "pollution-treatment-controls",
        "railroads",
        "rental-leasing-services",
        "security-protection-services",
        "specialty-business-services",
        "specialty-industrial-machinery",
        "staffing-employment-services",
        "tools-accessories",
        "trucking",
        "waste-management"
    ],

    "real-estate": [
        "real-estate-development",
        "real-estate-diversified",
        "real-estate-services",
        "reit-diversified",
        "reit-healthcare-facilities",
        "reit-hotel-motel",
        "reit-industrial",
        "reit-mortgage",
        "reit-office",
        "reit-residential",
        "reit-retail",
        "reit-specialty"
    ],

    "technology": [
        "communication-equipment",
        "computer-hardware",
        "consumer-electronics",
        "electronic-components",
        "electronics-computer-distribution",
        "information-technology-services",
        "scientific-technical-instruments",
        "semiconductor-equipment-materials",
        "semiconductors",
        "software-application",
        "software-infrastructure",
        "solar"
    ],

    "utilities": [
        "utilities-diversified",
        "utilities-independent-power-producers",
        "utilities-regulated-electric",
        "utilities-regulated-gas",
        "utilities-regulated-water",
        "utilities-renewable"
    ]
}

SECTOR_COLORS = {
    "basic-materials": "#1f77b4",    
    "communication-services": "#ff7f0e",
    "consumer-cyclical": "#2ca02c",
    "consumer-defensive": "#d62728",
    "energy": "#9467bd",
    "financial-services": "#8c564b",
    "healthcare": "#e377c2",
    "industrials": "#7f7f7f",
    "real-estate": "#bcbd22",
    "technology": "#17becf",
    "utilities": "#aec7e8"
}



def generate_portfolio_report(holdings: list, output_path: str, base_currency: str = "INR"):
    """
    Analyzes a list of stock holdings and generates a detailed PDF report.
    """
    console = Console()
    console.print("Generating portfolio report...", style="dim italic")
    if not holdings:
        print("Error: Holdings list is empty. Cannot generate report.")
        return

    try:
        df_consolidated = preprocess_holdings(holdings)
        
        unique_tickers = df_consolidated.index.tolist()
        market_data = fetch_market_data(unique_tickers)

        df_final, summary = perform_analysis(df_consolidated, market_data, base_currency)

        sector_donut_base64, others_table_html = create_sector_donut_chart(df_final)
        industry_list_html = generate_industry_list_html(df_final)

        html_content = generate_html_report(df_final, summary, sector_donut_base64, others_table_html, industry_list_html, base_currency)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            css_content = get_css_styles()
            full_html = html_content.replace("</head>", f"<style>{css_content}</style></head>")
            
            page.set_content(full_html)
            page.pdf(path=output_path, format="A4", print_background=True, margin={"top": "1cm", "right": "1cm", "bottom": "1cm", "left": "1cm"})
            browser.close()
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return


def preprocess_holdings(holdings: list) -> pd.DataFrame:
    """Converts the list of transactions into a consolidated DataFrame."""
    df = pd.DataFrame(holdings)
    df['total_cost'] = df['price'] * df['quantity']
    
    df_agg = df.groupby('ticker').agg(
        quantity=('quantity', 'sum'),
        total_cost=('total_cost', 'sum'),
        name=('name', 'first'),
        sector=('sector', 'first'),
        industry=('industry', 'first'),
        currency=('currency', 'first')
    )
    df_agg['weighted_avg_cost'] = df_agg['total_cost'] / df_agg['quantity']
    return df_agg

def fetch_market_data(tickers: list) -> dict:
    """Fetches current price for a list of tickers."""
    ticker_obj = Ticker(tickers, asynchronous=True)
    data = ticker_obj.price
    
    results = {}
    for ticker, ticker_data in data.items():
        current_price = ticker_data.get('regularMarketPrice', None)
        if current_price:
            results[ticker] = {'current_price': current_price}
        else:
            print(f"Warning: Could not fetch data for ticker '{ticker}'. It may be invalid or delisted.")
    return results

def perform_analysis(df: pd.DataFrame, market_data: dict, base_currency: str) -> tuple[pd.DataFrame, dict]:
    """Merges all data and calculates key portfolio metrics."""
    c = CurrencyConverter()
    df['current_price'] = df.index.map(lambda x: market_data.get(x, {}).get('current_price'))
    
    df.dropna(subset=['current_price'], inplace=True)
    if df.empty:
        raise ValueError("Could not fetch market price for any holdings.")

    def convert_to_base(row):
        local_market_value = row['current_price'] * row['quantity']
        cost_base = c.convert(row['total_cost'], row['currency'], base_currency)
        market_value_base = c.convert(local_market_value, row['currency'], base_currency)
        return pd.Series([cost_base, market_value_base])

    df[['total_cost_base', 'market_value_base']] = df.apply(convert_to_base, axis=1)
    
    df['gain_loss_base'] = df['market_value_base'] - df['total_cost_base']
    df['gain_loss_pct'] = (df['gain_loss_base'] / df['total_cost_base']).replace([np.inf, -np.inf], 0) * 100

    total_market_value = df['market_value_base'].sum()
    total_cost = df['total_cost_base'].sum()
    total_gain_loss = df['gain_loss_base'].sum()
    
    df['pct_of_portfolio'] = (df['market_value_base'] / total_market_value) * 100 if total_market_value else 0
    
    best_performer = df.loc[df['gain_loss_pct'].idxmax()]
    worst_performer = df.loc[df['gain_loss_pct'].idxmin()]

    summary = {
        "total_market_value": total_market_value, 
        "total_cost": total_cost,
        "total_gain_loss": total_gain_loss,
        "total_return_pct": (total_gain_loss / total_cost) * 100 if total_cost else 0,
        "best_performer_name": best_performer['name'], 
        "best_performer_pct": best_performer['gain_loss_pct'],
        "worst_performer_name": worst_performer['name'], 
        "worst_performer_pct": worst_performer['gain_loss_pct'],
    }
    
    return df.sort_values('market_value_base', ascending=False), summary

def create_sector_donut_chart(df: pd.DataFrame) -> tuple[str, str]:
    """
    Generates a sector allocation donut chart, grouping small slices into 'Others'.
    Returns the chart's base64 string and an HTML table for the 'Others' group.
    """
    total_market_value = df['market_value_base'].sum()
    if total_market_value == 0: return "", ""

    sector_pct = (df.groupby('sector')['market_value_base'].sum() / total_market_value) * 100
    sector_pct = sector_pct.sort_values(ascending=False)
    
    if sector_pct.empty: return "", ""

    sectors_to_plot_list = []
    remaining_sectors = sector_pct.copy()
    for sector, pct in sector_pct.items():
        remaining_sectors = remaining_sectors.drop(sector)
        sectors_to_plot_list.append(sector)
        if remaining_sectors.sum() < 5.0:
            break
            
    main_sectors = sector_pct.loc[sectors_to_plot_list]
    others = sector_pct.drop(sectors_to_plot_list)
    
    sectors_to_plot = main_sectors.copy()
    others_table_html = ""

    if not others.empty:
        sectors_to_plot['Others'] = others.sum()
        others_table_html = "<div class='others-table-container'><h4>'Others' Breakdown</h4><table class='others-table'><tbody>"
        for sector, pct in others.items():
            sector_display = sector.replace('-', ' ').title()
            others_table_html += f"<tr><td><b>{sector_display}</b></td><td class='text-right'><b>{pct:.2f}%</b></td></tr>"
        others_table_html += "</tbody></table></div>"

    plt.style.use('default') 
    fig, ax = plt.subplots(figsize=(10, 7), facecolor='white')
    
    chart_colors = [SECTOR_COLORS.get(sector, '#cccccc') for sector in sectors_to_plot.index]

    wedges, texts, autotexts = ax.pie(
        sectors_to_plot.values, 
        autopct='%1.1f%%', 
        startangle=90,
        pctdistance=0.85,
        wedgeprops=dict(width=0.4, edgecolor='w'),
        colors=chart_colors
    )
        
    legend_labels = [s.replace('-', ' ').title() for s in sectors_to_plot.index]
    ax.legend(wedges, legend_labels, title="Sectors", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    plt.setp(autotexts, size=10, weight="bold", color="#404040") 
    ax.axis('equal')
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    chart_html = f'<div class="chart-container"><img src="data:image/png;base64,{image_base64}" alt="Sector Allocation Chart"></div>'
    return chart_html, others_table_html

def generate_industry_list_html(df: pd.DataFrame) -> str:
    """Generates a robust HTML block structure for industry allocation."""
    industry_alloc = df.groupby(['sector', 'industry'])['pct_of_portfolio'].sum().reset_index()
    html = "<div class='industry-allocation-container'>"

    for sector, _ in SUPER_SECTOR_MAP.items():
        sector_data = industry_alloc[industry_alloc['sector'] == sector]
        if sector_data.empty:
            continue

        sector_display_name = sector.replace('-', ' ').title()
        html += f"""
        <div class='super-sector-block'>
            <div class='super-sector-header' style='background-color: {SECTOR_COLORS.get(sector, '#7f7f7f')};'>{sector_display_name}</div>
            <div class='industry-list'>"""
        
        for _, row in sector_data.iterrows():
            industry_display_name = row['industry'].replace('-', ' ').title()
            html += f"""
            <div class='industry-item'>
                <span class='industry-name'><b>{industry_display_name}</b></span>
                <span class='industry-pct'>{row['pct_of_portfolio']:.2f}%</span>
            </div>"""
        
        html += "</div></div>"
    html += "</div>"
    return html

def get_css_styles() -> str:
    """Returns the CSS styles for the PDF report."""
    css_string = ""
    with open("styles/style.css", 'r', encoding="utf-8") as f:
        css_string = f.read()
    return css_string

def generate_html_report(df_final, summary, sector_donut_base64, others_table_html, industry_list_html, base_currency):
    """Generates the full HTML content for the PDF report."""
    def format_currency(value): return f"{value:,.2f} {base_currency}"
    def format_gain(value): return f'<span class="{"positive" if value >= 0 else "negative"}">{value:,.2f} {base_currency}</span>'
    def format_pct(value): return f'<span class="{"positive" if value >= 0 else "negative"}">{value:.2f}%</span>'

    holdings_rows_html = ""
    for ticker, row in df_final.iterrows():
        sector_display = row['sector'].replace('-', ' ').title()
        holdings_rows_html += f"""
        <tr>
            <td>{row['name']}<br><small><b>({ticker})</b></small></td>
            <td>{sector_display}</td>
            <td class="text-right">{row['quantity']:,.0f}</td>
            <td class="text-right">{row['weighted_avg_cost']:,.2f} {row['currency']}</td>
            <td class="text-right">{row['current_price']:,.2f} {row['currency']}</td>
            <td class="text-right">{format_currency(row['market_value_base'])}</td>
            <td class="text-right">{format_gain(row['gain_loss_base'])}</td>
            <td class="text-right">{format_pct(row['gain_loss_pct'])}</td>
            <td class="text-right">{row['pct_of_portfolio']:.2f}%</td>
        </tr>"""

    return f"""
    <html>
        <head>
            <title>Portfolio Report</title>
            <meta charset="UTF-8">
        </head>
        <body>
            <h1>Portfolio Analysis Report</h1>
            <p class="header-date">
                <b>Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</b><br><br>
                <span class="currency-note">All values are reported in <b>{base_currency}</b></span>
            </p>
            <h2>Portfolio Overview</h2>
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="label">Total Market Value</div>
                    <div class="value">{format_currency(summary['total_market_value'])}</div>
                </div>
                <div class="summary-item">
                    <div class="label">Total Gain / Loss</div>
                    <div class="value">{format_gain(summary['total_gain_loss'])} ({format_pct(summary['total_return_pct'])})</div>
                </div>
                <div class="summary-item">
                    <div class="label">Best Performer</div>
                    <div class="value">{summary['best_performer_name']} ({format_pct(summary['best_performer_pct'])})</div>
                </div>
                <div class="summary-item">
                    <div class="label">Worst Performer</div>
                    <div class="value">{summary['worst_performer_name']} ({format_pct(summary['worst_performer_pct'])})</div>
                </div>
            </div>
            <h2>Diversification</h2>
            <div class="diversification-section">
                <h3>Sector Allocation</h3>
                <div class="chart-and-others-wrapper">
                    {sector_donut_base64}
                    {others_table_html}
                </div>
                <h3>Industry Allocation</h3>
                {industry_list_html}
            </div>
            <h2>Holdings Details</h2>
            <table>
                <thead>
                    <tr>
                        <th>Name (Ticker)</th>
                        <th>Sector</th>
                        <th class="text-right">Quantity</th>
                        <th class="text-right">Avg. Cost</th>
                        <th class="text-right">Current Price</th>
                        <th class="text-right">Market Value</th>
                        <th class="text-right">Gain/Loss</th>
                        <th class="text-right">Return %</th>
                        <th class="text-right">% of Portfolio</th>
                    </tr>
                </thead>
                <tbody>{holdings_rows_html}</tbody>
            </table>
        </body>
    </html>"""

