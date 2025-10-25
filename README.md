# Conversational AI Financial Advisor

<p align="center"><b>An advanced conversational AI agent built with LangGraph and Streamlit.</b></p>
<p align="center">
This agent acts as a personal financial advisor, understanding natural language commands to provide deep market analysis, manage portfolios, and generate personalized investment advice.
</p>

<p align="center">
<img alt="Python" src="https://img.shields.io/badge/Python-3.11%2B-blue?style=for-the-badge&logo=python&logoColor=white"/>
<img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-1.30%2B-red?style=for-the-badge&logo=streamlit&logoColor=white"/>
<img alt="LangGraph" src="https://img.shields.io/badge/LangGraph-0.1%2B-blueviolet?style=for-the-badge&logo=langchain&logoColor=white"/>
<img alt="Gemini" src="https://img.shields.io/badge/Google%20Gemini-API-orange?style=for-the-badge&logo=google&logoColor=white"/>
</p>

---

## 📸 Screenshots

**Profile Creation**  
*Caption: Users create a personal investment profile (risk tolerance, age, horizon) for tailored advice.*  
`ADD_SCREENSHOT_HERE`

**Main Chat Interface**  
*Caption: The main chat interface where users can ask complex financial questions.*  
`ADD_SCREENSHOT_HERE`

**Stock Analysis**  
*Caption: A deep-dive analysis of a specific stock, including trends, valuation, and a final recommendation.*  
`ADD_SCREENSHOT_HERE`

**Portfolio Report**  
*Caption: The agent can generate and provide a download link for a full PDF portfolio report.*  
`ADD_SCREENSHOT_HERE`

---

## 🎥 Project Demo

Watch a full walkthrough and demonstration of the project's capabilities on [YouTube](YOUR_YOUTUBE_LINK_HERE).

---

## 🤖 About The Project

This project is a sophisticated, multi-tool financial agent built on **LangGraph**, designed to function as an expert financial advisor in a conversational chat interface powered by **Streamlit**.

The core agent (in `agents/process_input.py`) acts as a "supervisor" or "router," analyzing the user's prompt and personal profile to select the best tool for the request. The agent personalizes its responses based on the user's age, risk tolerance, and investment horizon (from `Database/settings.json`).

---

## ✨ Core Features

### 1. 📈 In-Depth Stock & Fund Analysis (`stock_analyzer`)
- **Deep-Dive Analysis:** Complete fundamental and technical analysis of equities and mutual funds.  
- **Data Aggregation:** Pulls extensive financial data via `yahooquery`.  
- **AI-Powered Synthesis:** LLM-based trend analysis and financial health evaluation (`super_analysis_EQUITY.py`).  
- **Personalized Advice:** Generates Buy/Sell/Hold recommendations aligned with the user's profile (`super_investment_advisor_EQUITY.py`).

### 2. 🗂️ Portfolio Management (CRUD)
- **Add Holdings:** `add_holding` – add new transactions (buy/sell).  
- **View Holdings:** `list_holdings` – display current transactions.  
- **Update Holdings:** `update_holding` – modify existing transactions.  
- **Delete Holdings:** `delete_holding_by_name` / `delete_holding_by_transaction_id`.  
- **Clear Portfolio:** `clear_holdings`.  

*(Portfolio data stored locally in `Database/holdings.json`)*

### 3. 📑 Portfolio Analysis & Recommendation
- **Holistic Statistics:** `get_portfolio_statistics` – total portfolio value, beta, sector exposure.  
- **PDF Report:** `generate_portfolio_report` – download a full multi-page report.  
- **AI Recommendations:** `portfolio_recommendation` – portfolio rebalancing and allocation advice.

### 4. 📊 Market & Data Retrieval
- **Stock Screener:** `stock_screener` – filter stocks by P/E ratio, market cap, etc.  
- **Financial News:** `display_financial_news` – latest news per company.  
- **Market Performance:** `get_sector_returns` / `get_industry_returns`.  
- **Price History:** `get_historical_pricing`.  
- **Utility:** `get_tickers` – find stock tickers by company name.

---

## 🏗️ Architecture & Tech Stack

- **Application Framework:** Streamlit  
- **Agent Framework:** LangGraph  
- **LLM:** Google Gemini via `langchain_google_genai`  
- **Financial Data:** `yahooquery`  
- **Data Handling:** Pandas  
- **PDF Generation:** ReportLab  

### Agent Flow
1. **StateGraph Start:** User enters prompt via Streamlit UI.  
2. **parse_user_input Node:** Supervisor agent analyzes intent and chooses the best tool.  
3. **tool_executor Node:** Executes the selected tool.  
4. **Tool Execution:** Runs the full logic, fetches data, and processes analysis.  
5. **Return Value:** Markdown or PDF report path returned.  
6. **route_to_next_tool:** Router directs to END node.  
7. **Streamlit UI:** Renders Markdown or PDF link for the user.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+  
- Google Gemini API key (or other LLM)

### Installation
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME

# Create a virtual environment
python -m venv venv
# Activate it
# macOS/Linux
source venv/bin/activate
# Windows
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
