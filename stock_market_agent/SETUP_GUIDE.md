# 📋 Project Setup Guide — Stock Market Intelligence Agent

Step-by-step guide to recreate this project from scratch.
Track 2 Project Submission — Connect AI Agents to Real-World Data using MCP.

---

## 🏗️ What We Are Building

A Stock Market Intelligence Agent that:
- Uses **Google ADK** as the agent framework
- Connects to a **custom MCP server** via Model Context Protocol
- Fetches **live stock data** from Yahoo Finance (no API key needed)
- Deployed on **Google Cloud Run** as a serverless container
- Returns structured professional stock analysis using **Gemini 2.5 Flash**

---

## 📁 Final Project Structure

```
stock_market_agent/
├── mcp_server.py              # Custom MCP server — Yahoo Finance tools
├── startup.sh                 # Starts MCP server + ADK agent
├── Dockerfile                 # Cloud Run container definition
├── requirements.txt           # Python dependencies
├── .env.example               # Config template (safe to commit)
├── .gitignore                 # Excludes .env and venv
├── README.md                  # Project documentation
└── stock_market_agent/        # ADK agent package
    ├── agent.py               # Agent definition + MCP connection
    ├── __init__.py            # ADK package marker
    └── .env                   # Runtime config (NOT committed)
```

---

## 🔧 Prerequisites

- Google Cloud account with billing enabled
- Google Cloud project with these APIs enabled:
  - Vertex AI API
  - Cloud Run API
  - Artifact Registry API
  - Cloud Build API
  - Compute Engine API
- Cloud Shell (recommended) or local environment with Python 3.12

---

## 🚀 Step-by-Step Setup

### Step 1 — Set up Google Cloud project

```bash
# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  aiplatform.googleapis.com \
  compute.googleapis.com
```

---

### Step 2 — Create project directory

```bash
mkdir ~/stock_market_agent
cd ~/stock_market_agent
mkdir stock_market_agent
```

---

### Step 3 — Create requirements.txt

```bash
cat > requirements.txt << 'EOF'
google-adk==1.14.0
yfinance==0.2.54
mcp[cli]==1.9.0
fastmcp==2.3.3
python-dotenv==1.1.0
uvicorn==0.29.0
google-cloud-logging
EOF
```

---

### Step 4 — Create the MCP Server (mcp_server.py)

The MCP server exposes two tools:
- `get_stock_price` — fetches live price and key metrics
- `get_stock_summary` — fetches business summary and analyst recommendations

```bash
cat > mcp_server.py << 'EOF'
"""
Stock Market MCP Server
Exposes live stock data from Yahoo Finance as MCP tools.
"""

import json
import logging
import sys
import uvicorn
import yfinance as yf
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("stock-market-server")


@mcp.tool()
def get_stock_price(ticker: str) -> str:
    """
    Fetches the current live stock price and key metrics for a given ticker symbol.
    Args:
        ticker: Stock ticker symbol e.g. AAPL, GOOGL, MSFT, TSLA
    Returns:
        JSON string with current price, change, volume, market cap and other key metrics.
    """
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info

        if not info or ("currentPrice" not in info and "regularMarketPrice" not in info):
            return json.dumps({
                "error": f"Could not fetch data for ticker '{ticker}'. Please check the symbol."
            })

        price = info.get("currentPrice") or info.get("regularMarketPrice", "N/A")
        prev_close = info.get("previousClose", "N/A")
        change = round(price - prev_close, 2) if price != "N/A" and prev_close != "N/A" else "N/A"
        change_pct = round((change / prev_close) * 100, 2) if change != "N/A" and prev_close != 0 else "N/A"

        result = {
            "ticker": ticker.upper(),
            "company_name": info.get("longName", "N/A"),
            "current_price": price,
            "currency": info.get("currency", "USD"),
            "previous_close": prev_close,
            "price_change": change,
            "price_change_pct": f"{change_pct}%" if change_pct != "N/A" else "N/A",
            "day_high": info.get("dayHigh", "N/A"),
            "day_low": info.get("dayLow", "N/A"),
            "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "52_week_low": info.get("fiftyTwoWeekLow", "N/A"),
            "volume": info.get("volume", "N/A"),
            "avg_volume": info.get("averageVolume", "N/A"),
            "market_cap": info.get("marketCap", "N/A"),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "eps": info.get("trailingEps", "N/A"),
            "dividend_yield": info.get("dividendYield", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
        }

        logger.info(f"[MCP] Fetched stock data for {ticker.upper()}")
        return json.dumps(result, default=str)

    except Exception as e:
        logger.error(f"[MCP] Error fetching {ticker}: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_stock_summary(ticker: str) -> str:
    """
    Fetches a business summary and analyst recommendation for a given stock ticker.
    Args:
        ticker: Stock ticker symbol e.g. AAPL, GOOGL, MSFT, TSLA
    Returns:
        JSON string with business description and analyst recommendation.
    """
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info

        result = {
            "ticker": ticker.upper(),
            "company_name": info.get("longName", "N/A"),
            "business_summary": info.get("longBusinessSummary", "N/A"),
            "analyst_recommendation": info.get("recommendationKey", "N/A"),
            "target_high_price": info.get("targetHighPrice", "N/A"),
            "target_low_price": info.get("targetLowPrice", "N/A"),
            "target_mean_price": info.get("targetMeanPrice", "N/A"),
            "number_of_analyst_opinions": info.get("numberOfAnalystOpinions", "N/A"),
        }

        logger.info(f"[MCP] Fetched summary for {ticker.upper()}")
        return json.dumps(result, default=str)

    except Exception as e:
        logger.error(f"[MCP] Error fetching summary for {ticker}: {e}")
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    logger.info(f"Starting Stock Market MCP Server on port {port}")
    app = mcp.http_app(path="/mcp")
    uvicorn.run(app, host="0.0.0.0", port=port)
EOF
```

---

### Step 5 — Create the ADK Agent package

#### 5a — Create __init__.py

```bash
cat > stock_market_agent/__init__.py << 'EOF'
from . import agent
EOF
```

#### 5b — Create agent.py

```bash
cat > stock_market_agent/agent.py << 'EOF'
"""
Stock Market Intelligence Agent
ADK agent that connects to the Stock Market MCP server
and provides live stock analysis using Gemini 2.5 Flash.
"""

import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

load_dotenv()

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:5000/mcp")
MODEL = os.getenv("MODEL", "gemini-2.5-flash")

stock_mcp_toolset = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=MCP_SERVER_URL,
        timeout=30.0
    )
)

root_agent = Agent(
    name="stock_market_agent",
    model=MODEL,
    description=(
        "A professional Stock Market Intelligence Agent that fetches live stock data "
        "and provides concise, structured financial analysis."
    ),
    instruction="""
You are a professional Stock Market Intelligence Agent.

When a user asks about a stock or company, follow this exact process:

STEP 1 — Identify the ticker symbol
- If the user provides a company name (e.g. "Apple"), map it to the correct ticker (e.g. AAPL)
- Common mappings: Apple=AAPL, Google/Alphabet=GOOGL, Microsoft=MSFT, Tesla=TSLA,
  Amazon=AMZN, Meta=META, Netflix=NFLX, Nvidia=NVDA, Samsung=005930.KS

STEP 2 — Fetch data
- Call get_stock_price to get live price and key metrics
- Call get_stock_summary to get business description and analyst recommendations

STEP 3 — Generate analysis in this exact format:

---
## 📊 Stock Analysis: [COMPANY NAME] ([TICKER])

### 💰 Current Price
**[PRICE] [CURRENCY]** | Change: [CHANGE] ([CHANGE_PCT])

### 📈 Key Metrics
| Metric | Value |
|--------|-------|
| Day High / Low | [HIGH] / [LOW] |
| 52-Week High / Low | [52H] / [52L] |
| Market Cap | [MARKET_CAP] |
| P/E Ratio | [PE] |
| EPS | [EPS] |
| Volume | [VOLUME] |
| Avg Volume | [AVG_VOLUME] |
| Dividend Yield | [DIVIDEND] |

### 🏢 Company Overview
[2-3 sentence business summary]

### 📉 Analyst Outlook
- **Recommendation:** [RECOMMENDATION]
- **Price Target Range:** [LOW] — [HIGH]
- **Consensus Target:** [MEAN]
- **Analyst Opinions:** [NUMBER]

### 💡 Brief Analysis
[3-4 sentences of professional analysis]

---

Rules:
- Always use real data from the tools — never fabricate numbers
- If data is unavailable for a field, show N/A
- Keep the analysis professional and factual
- Do not provide financial advice or buy/sell recommendations
- Add disclaimer: "This analysis is for informational purposes only."
""",
    tools=[stock_mcp_toolset],
)
EOF
```

#### 5c — Create .env

```bash
cat > stock_market_agent/.env << 'EOF'
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
GOOGLE_CLOUD_LOCATION=us-central1
MODEL=gemini-2.5-flash
MCP_SERVER_URL=http://127.0.0.1:5000/mcp
EOF
```

Replace `YOUR_PROJECT_ID` with your actual project ID.

---

### Step 6 — Create Dockerfile

```bash
cat > Dockerfile << 'EOF'
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY mcp_server.py .
COPY startup.sh .
COPY stock_market_agent/ ./stock_market_agent/
RUN chmod +x startup.sh
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["./startup.sh"]
EOF
```

---

### Step 7 — Create startup.sh

```bash
cat > startup.sh << 'EOF'
#!/bin/bash
python /app/mcp_server.py 5000 &
sleep 5
export MCP_SERVER_URL="http://127.0.0.1:5000/mcp"
export GOOGLE_GENAI_USE_VERTEXAI=1
export GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
export GOOGLE_CLOUD_LOCATION=us-central1
export MODEL=gemini-2.5-flash
cd /app
adk web --host 0.0.0.0 --port ${PORT:-8080}
EOF
chmod +x startup.sh
```

---

### Step 8 — Create .gitignore and .env.example

```bash
cat > .gitignore << 'EOF'
.env
*.env
**/.env
.venv/
__pycache__/
*.pyc
.adk/
**/.adk/
EOF

cat > .env.example << 'EOF'
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
MODEL=gemini-2.5-flash
MCP_SERVER_URL=http://127.0.0.1:5000/mcp
EOF
```

---

### Step 9 — Create virtual environment and test locally

```bash
# Create venv
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Tab 1 — Start MCP Server
python mcp_server.py

# Tab 2 — Start ADK Agent
export MCP_SERVER_URL="http://127.0.0.1:5000/mcp"
export GOOGLE_GENAI_USE_VERTEXAI=1
export GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
export GOOGLE_CLOUD_LOCATION=us-central1
adk web --host 0.0.0.0 --port 8080 --allow_origins "*"
```

Open Web Preview → port 8080 → test with:
```
Analyse AAPL for me
```

---

### Step 10 — Create IAM Service Account

```bash
PROJECT_ID=YOUR_PROJECT_ID
SA_NAME=stock-agent-sa
SERVICE_ACCOUNT=${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com

# Create service account
gcloud iam service-accounts create ${SA_NAME} \
  --display-name="Stock Market Agent SA" \
  --project=${PROJECT_ID}

# Grant Vertex AI permissions
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/aiplatform.user"
```

---

### Step 11 — Deploy to Cloud Run

```bash
PROJECT_ID=YOUR_PROJECT_ID
SA_NAME=stock-agent-sa
SERVICE_ACCOUNT=${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com
REGION=us-central1

gcloud run deploy stock-market-agent \
  --source . \
  --region ${REGION} \
  --project ${PROJECT_ID} \
  --service-account ${SERVICE_ACCOUNT} \
  --set-env-vars GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION},GOOGLE_GENAI_USE_VERTEXAI=1,MODEL=gemini-2.5-flash,MCP_SERVER_URL=http://127.0.0.1:5000/mcp \
  --allow-unauthenticated \
  --timeout=300
```

When prompted:
- Create Artifact Registry repository? → `Y`
- Allow unauthenticated invocations? → `y`

Deployment takes 5-7 minutes. You will receive a public URL:
```
https://stock-market-agent-XXXXXXXXXX.us-central1.run.app
```

---

### Step 12 — Verify deployment

Open the Cloud Run URL in browser:
```
https://your-cloud-run-url/dev-ui/
```

Toggle Token Streaming ON → Select `stock_market_agent` → Type:
```
Analyse AAPL for me
```

---

### Step 13 — Push to GitHub

Create a new repo at github.com/new:
- Name: `stock-market-agent`
- Visibility: Public
- Empty — no README

Then:

```bash
cd ~/stock_market_agent

git init
git add .
git commit -m "Stock Market Intelligence Agent — ADK + MCP + Cloud Run"
git branch -m main
git remote add origin https://github.com/YOUR_USERNAME/stock-market-agent.git
git push -u origin main
```

Use your Personal Access Token (ghp_...) when prompted for password.

---

## 🧪 Sample Test Queries

```
1. Analyse AAPL for me
2. What is the current stock price of Tesla?
3. Give me a full analysis of Microsoft
4. How is Nvidia performing today?
5. What are analysts saying about Amazon stock?
```

---

## ⚠️ Known Issues and Fixes

### Issue 1 — FastMCP.run() unexpected keyword argument 'host'
FastMCP 2.3.3 changed the API. Fix:
```python
# Wrong
mcp.run(transport="streamable-http", host="0.0.0.0", port=port)

# Correct
app = mcp.http_app(path="/mcp")
uvicorn.run(app, host="0.0.0.0", port=port)
```

### Issue 2 — No agents found in current folder
ADK discovers agents from the current working directory.
Always run `adk web` from the parent folder containing the agent package:
```bash
cd ~/stock_market_agent   ← correct
adk web --host 0.0.0.0 --port 8080 --allow_origins "*"
```

### Issue 3 — Billing project limit
Google limits billing to 5 projects per account.
Reuse an existing project instead of creating a new one.

### Issue 4 — Cloud Run showing No agents found
The startup.sh must `cd /app` before running `adk web`.
ADK discovers agents relative to the current working directory.

---

## 🧹 Cleanup

```bash
gcloud run services delete stock-market-agent \
  --region=us-central1 \
  --project=YOUR_PROJECT_ID \
  --quiet

gcloud artifacts repositories delete cloud-run-source-deploy \
  --location=us-central1 \
  --project=YOUR_PROJECT_ID \
  --quiet
```

---

## 📚 References

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [yfinance Documentation](https://github.com/ranaroussi/yfinance)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Vertex AI Gemini Models](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models)
