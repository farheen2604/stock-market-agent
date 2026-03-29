# 📈 Stock Market Intelligence Agent

An AI-powered Stock Market Intelligence Agent built with **Google ADK** and **Gemini 2.5 Flash**, connected to a custom **MCP server** that fetches live stock data from Yahoo Finance. Deployed as a serverless service on **Google Cloud Run**.

This is the Project 2 submission for the *Connect AI Agents to Real-World Data using MCP* track.

---

## 🤖 What It Does

The agent accepts any stock ticker or company name and returns a structured professional analysis:

- **Live price** with daily change and percentage
- **Key metrics** — Market Cap, P/E Ratio, EPS, Volume, 52-week range
- **Company overview** — business summary from live data
- **Analyst outlook** — recommendation, price targets, consensus

### Example Input
```
Analyse AAPL for me
```

### Example Output
```
## 📊 Stock Analysis: Apple Inc. (AAPL)

### 💰 Current Price
$189.30 USD | Change: +1.25 (+0.67%)

### 📈 Key Metrics
| Metric          | Value         |
|-----------------|---------------|
| Day High / Low  | $190.5 / $187.2 |
| 52-Week High/Low| $199.6 / $164.1 |
| Market Cap      | $2.94T        |
| P/E Ratio       | 31.2          |
| EPS             | $6.07         |
| Volume          | 52.3M         |
| Dividend Yield  | 0.52%         |

### 💡 Brief Analysis
Apple is currently trading near the upper range of its 52-week band,
suggesting sustained investor confidence. The P/E of 31.2 reflects a
premium valuation typical of large-cap tech. Volume is above average,
indicating active participation. Analyst consensus remains bullish with
a mean price target above current levels.

⚠️ This analysis is for informational purposes only and does not
constitute financial advice.
```

---

## 🏗️ Architecture

```
User Request (HTTP)
        │
        ▼
Cloud Run Service
        │
        ├── ADK Agent (port 8080)
        │   └── root_agent (Gemini 2.5 Flash via Vertex AI)
        │           │
        │           ▼ MCP StreamableHTTP
        └── MCP Server (port 5000)
                └── Yahoo Finance API (live data, no API key needed)
                    Tools:
                    ├── get_stock_price()
                    └── get_stock_summary()
```

**Key design decision:** Both the MCP server and ADK agent run in the same
Cloud Run container, started via a shell script. The MCP server starts first
on port 5000, the ADK agent starts on port 8080 and connects to it internally.

---

## 📁 Project Structure

```
stock_market_agent/
├── mcp_server.py              # Custom MCP server — Yahoo Finance tools
├── startup.sh                 # Starts MCP server + ADK agent
├── Dockerfile                 # Cloud Run container definition
├── requirements.txt           # Python dependencies
├── .env.example               # Config template
├── .gitignore
├── README.md
└── stock_market_agent/        # ADK agent package
    ├── agent.py               # Agent definition + MCP connection
    ├── __init__.py            # ADK package marker
    └── .env                   # Runtime config (not committed)
```

---

## 🚀 Setup & Deployment

### Prerequisites
- Google Cloud project with billing enabled
- Cloud Shell
- APIs enabled: Vertex AI, Cloud Run, Artifact Registry, Cloud Build

### Step 1 — Enable APIs
```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  aiplatform.googleapis.com \
  compute.googleapis.com
```

### Step 2 — Clone the repo
```bash
git clone https://github.com/farheen2604/stock-market-agent.git
cd stock-market-agent
```

### Step 3 — Test locally

**Tab 1 — Start MCP Server:**
```bash
pip install -r requirements.txt
python mcp_server.py
```

**Tab 2 — Start ADK Agent:**
```bash
export MCP_SERVER_URL="http://127.0.0.1:5000/mcp"
adk web --host 0.0.0.0 --port 8080 --allow_origins "*" stock_market_agent/
```

Open Web Preview → port 8080

### Step 4 — Deploy to Cloud Run
```bash
PROJECT_ID=project2-stock-market-agent
SA_NAME=stock-agent-sa
SERVICE_ACCOUNT=${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com
REGION=us-central1

# Create service account
gcloud iam service-accounts create ${SA_NAME} \
    --display-name="Stock Market Agent Service Account" \
    --project=${PROJECT_ID}

# Grant permissions
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/aiplatform.user"

# Deploy
gcloud run deploy stock-market-agent \
  --source . \
  --region ${REGION} \
  --project ${PROJECT_ID} \
  --service-account ${SERVICE_ACCOUNT} \
  --set-env-vars GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION},GOOGLE_GENAI_USE_VERTEXAI=1,MODEL=gemini-2.5-flash,MCP_SERVER_URL=http://127.0.0.1:5000/mcp \
  --allow-unauthenticated \
  --timeout=300
```

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

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Agent Framework | Google ADK (google-adk 1.14.0) |
| LLM | Gemini 2.5 Flash via Vertex AI |
| MCP Server | Custom FastMCP server (mcp + fastmcp) |
| Data Source | Yahoo Finance API (yfinance) |
| Deployment | Google Cloud Run (serverless) |
| Container Build | Google Cloud Build |
| Auth | IAM Service Account (roles/aiplatform.user) |
| Language | Python 3.12 |

---

## 🧹 Cleanup

```bash
gcloud run services delete stock-market-agent \
  --region=us-central1 \
  --project=project2-stock-market-agent \
  --quiet
```

---

## 📚 References

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [yfinance Documentation](https://github.com/ranaroussi/yfinance)
- [Vertex AI Gemini Models](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models)
