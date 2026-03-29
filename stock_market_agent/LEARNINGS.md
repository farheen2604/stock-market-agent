# 📚 Learnings & Troubleshooting — Stock Market Intelligence Agent

Project 2 — Track 2: Connect AI Agents to Real-World Data using MCP
Built with Google ADK, FastMCP, Yahoo Finance, and Google Cloud Run.

---

## 🧠 Key Learnings

### 1. What is Model Context Protocol (MCP)?
MCP is a standardized protocol that allows AI agents to connect to external
tools and data sources in a structured, secure way. Instead of hardcoding
API calls inside the agent, MCP separates the AI reasoning layer from the
tool execution layer.

Key benefits:
- Agent doesn't need to know HOW to call an API — it just calls a tool
- Tools can be reused across multiple agents and frameworks
- Centralized tool management — update tools without redeploying the agent
- Standardized interface — any MCP-capable client can connect

### 2. Custom MCP Server vs Google-hosted MCP
There are two ways to use MCP with ADK:

| Approach | Example | When to use |
|---|---|---|
| Google-hosted remote MCP | Maps, BigQuery endpoints | Connecting to Google services |
| Custom self-hosted MCP | This project (FastMCP) | Connecting to any external API |

In this project we built a **custom MCP server** using FastMCP that wraps
Yahoo Finance API — making live stock data available to the ADK agent as
a structured tool.

### 3. Architecture Pattern — Two Services in One Container
For Cloud Run deployment, we ran both services inside one container:
- MCP Server on port 5000 (started by startup.sh in background)
- ADK Agent on port 8080 (started after MCP server is ready)

This is a valid pattern for simple deployments where both services
need to communicate on localhost. For production at scale, you would
separate them into two Cloud Run services.

### 4. ADK Agent Discovery
ADK discovers agent packages from the **current working directory**.
It looks for Python packages (folders with `__init__.py`) that contain
a `root_agent` variable.

Critical rule:
- Always run `adk web` from the parent folder containing the agent package
- The agent package must have both `__init__.py` AND `agent.py` with `root_agent`

### 5. FastMCP Version Differences
FastMCP API changes between versions:

| Version | Run command |
|---|---|
| < 2.0 | `mcp.run(transport="streamable-http", host="0.0.0.0", port=port)` |
| 2.3.3+ | `app = mcp.http_app(path="/mcp")` then `uvicorn.run(app, host=..., port=...)` |

Always check the version before using the run command.

### 6. Yahoo Finance via yfinance
Yahoo Finance provides free, no-API-key-required access to live stock data.
The `yfinance` library wraps this into a clean Python interface.

Key data available:
- currentPrice, previousClose, dayHigh, dayLow
- fiftyTwoWeekHigh, fiftyTwoWeekLow
- marketCap, trailingPE, trailingEps
- volume, averageVolume, dividendYield
- longBusinessSummary, recommendationKey
- targetHighPrice, targetLowPrice, targetMeanPrice

### 7. Cloud Run Deployment with Source
The `gcloud run deploy --source .` command automates:
1. Building a Docker container from your Dockerfile
2. Pushing it to Artifact Registry
3. Deploying it to Cloud Run
4. Configuring IAM and networking

No need to manually build or push Docker images.

---

## 🛠️ Issues Faced and Fixes

### Issue 1 — FastMCP.run() unexpected keyword argument 'host'

**Error:**
```
TypeError: FastMCP.run() got an unexpected keyword argument 'host'
```

**Why it occurred:**
FastMCP 2.3.3 changed its API. The `run()` method no longer accepts
`host`, `port`, or `path` arguments directly. These must now be passed
to `uvicorn.run()` separately after creating an HTTP app instance.

**Fix:**
```python
# Wrong (old API)
mcp.run(transport="streamable-http", host="0.0.0.0", port=port, path="/mcp")

# Correct (FastMCP 2.3.3+)
app = mcp.http_app(path="/mcp")
uvicorn.run(app, host="0.0.0.0", port=port)
```

**Also install uvicorn separately:**
```bash
pip install uvicorn
```

**How to avoid next time:**
Always check FastMCP version before using:
```bash
pip show fastmcp | grep Version
```
Then check the FastMCP changelog for the correct run() API.

---

### Issue 2 — No agents found in current folder (locally)

**Error:**
```
Warning: No agents found in current folder.
Failed to load agents.
```

**Why it occurred:**
`adk web` was run from the wrong directory. ADK discovers agent packages
by scanning the current working directory for Python packages containing
a `root_agent`. Running from a subdirectory or wrong parent folder means
ADK cannot find the package.

**Fix:**
```bash
# Wrong — running from inside the agent package
cd ~/stock_market_agent/stock_market_agent
adk web ...

# Correct — running from the parent folder
cd ~/stock_market_agent
adk web --host 0.0.0.0 --port 8080 --allow_origins "*"
```

**How to avoid next time:**
Always verify your directory before running adk web:
```bash
pwd                          # Should be ~/stock_market_agent
ls stock_market_agent/       # Should show agent.py and __init__.py
adk web ...
```

---

### Issue 3 — No agents found on Cloud Run

**Error:**
```
Warning: No agents found in current folder (on deployed Cloud Run service)
```

**Why it occurred:**
The startup.sh was passing `stock_market_agent/` as an argument to
`adk web`, but `adk web` does not accept a path argument. It only
discovers agents from the current working directory. The container
working directory was `/app` but the agent discovery was failing
because the command was wrong.

**Fix:**
```bash
# Wrong startup.sh
adk web --host 0.0.0.0 --port ${PORT:-8080} stock_market_agent/

# Correct startup.sh
cd /app
adk web --host 0.0.0.0 --port ${PORT:-8080}
```

The key insight: `cd /app` before running `adk web` ensures ADK
scans `/app` and finds the `stock_market_agent` package there.

**How to avoid next time:**
Always test the exact startup command locally first:
```bash
cd ~/stock_market_agent
adk web --host 0.0.0.0 --port 8080 --allow_origins "*"
```
If it works locally, replicate the exact same `cd` + `adk web`
pattern in startup.sh.

---

### Issue 4 — Billing project limit

**Error:**
```
Unable to enable billing.
You have reached the limit of projects on which you can enable billing.
```

**Why it occurred:**
Google Cloud free tier limits the number of projects that can have
billing enabled simultaneously (typically 5). Creating a new project
for every lab exhausts this limit quickly.

**Fix:**
Reuse an existing project that already has billing enabled:
```bash
# List existing projects
gcloud projects list

# Switch to existing project with billing
gcloud config set project EXISTING_PROJECT_ID
```

**How to avoid next time:**
- Use one project per track, not one per lab
- Delete completed lab projects promptly to free up billing slots
- Check billing quota before creating new projects:
```bash
gcloud billing accounts list
```

---

### Issue 5 — Cloud Build PERMISSION_DENIED

**Error:**
```
PERMISSION_DENIED: Build failed because the default service account
is missing required IAM permissions.
```

**Why it occurred:**
When using `gcloud run deploy --source .`, Cloud Build needs permissions
to write to Cloud Storage (to upload source code) and to write logs.
The default compute service account was missing `storage.admin` and
`logging.logWriter` roles.

**Fix:**
```bash
PROJECT_NUMBER=your-project-number

# Grant storage permissions to compute SA
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/storage.admin"

# Grant logging permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/logging.logWriter"

# Grant storage to Cloud Build SA
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/storage.admin"
```

**How to avoid next time:**
Run this permissions setup script at the start of every new project
before attempting Cloud Run deployment.

---

### Issue 6 — Port already in use

**Error:**
```
ERROR: [Errno 98] error while attempting to bind on address ('0.0.0.0', 8080):
address already in use
```

**Why it occurred:**
A previous `adk web` process was still running on port 8080 from an
earlier session that wasn't properly terminated.

**Fix:**
```bash
# Kill process on port 8080
fuser -k 8080/tcp

# Then restart
adk web --host 0.0.0.0 --port 8080 --allow_origins "*"

# Or use a different port
adk web --host 0.0.0.0 --port 8090 --allow_origins "*"
```

**How to avoid next time:**
Always use Ctrl+C to cleanly stop `adk web` before restarting.
If session crashed, use `fuser -k PORT/tcp` to free the port.

---

### Issue 7 — gcloud authentication lost

**Error:**
```
You do not currently have an active account selected.
Please run: gcloud auth login
```

**Why it occurred:**
Cloud Shell sessions time out after periods of inactivity. When the
session restarts, gcloud authentication is lost and must be renewed.

**Fix:**
```bash
gcloud auth login
gcloud config set account farheen.learning264@gmail.com
gcloud config set project YOUR_PROJECT_ID
```

**How to avoid next time:**
At the start of every Cloud Shell session, always run:
```bash
gcloud auth list           # Check if authenticated
gcloud config get-value project  # Check active project
```
If not authenticated, run `gcloud auth login` immediately.

---

### Issue 8 — Git push "repository not found"

**Error:**
```
remote: Repository not found.
fatal: repository 'https://github.com/USERNAME/REPO.git/' not found
```

**Why it occurred:**
The GitHub repository was not created before attempting to push.
`git remote add origin` only sets the URL locally — it does not
create the repository on GitHub.

**Fix:**
1. Go to github.com/new
2. Create the repository with the exact same name
3. Keep it completely empty — no README, no .gitignore
4. Then run `git push -u origin main`

**How to avoid next time:**
Always create the GitHub repo BEFORE running git commands.
Order of operations:
1. Create repo on GitHub (empty)
2. `git init` locally
3. `git add .` and `git commit`
4. `git remote add origin URL`
5. `git push`

---

### Issue 9 — Git push "src refspec main does not match"

**Error:**
```
error: src refspec main does not match any
```

**Why it occurred:**
Git initialized with `master` as the default branch name, but the
push command specified `main`. The branch hadn't been renamed yet,
or no commits had been made yet so the branch didn't exist.

**Fix:**
```bash
# Rename branch
git branch -m master main

# Or if no commits made yet, commit first then rename
git add .
git commit -m "initial commit"
git branch -m master main
git push -u origin main
```

**How to avoid next time:**
Set default branch name globally once:
```bash
git config --global init.defaultBranch main
```
All future repos will use `main` automatically.

---

## ✅ Pre-Project Checklist

Run these before starting any new ADK + Cloud Run project:

```bash
# 1. Check authentication
gcloud auth list

# 2. Set correct project
gcloud config set project YOUR_PROJECT_ID

# 3. Enable all required APIs
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  aiplatform.googleapis.com \
  compute.googleapis.com

# 4. Set default git branch name
git config --global init.defaultBranch main

# 5. Set git identity
git config --global user.email "your@email.com"
git config --global user.name "yourusername"

# 6. Check FastMCP version before using
pip show fastmcp | grep Version

# 7. Always test locally before deploying
# Tab 1: python mcp_server.py
# Tab 2: cd ~/project && adk web --host 0.0.0.0 --port 8080 --allow_origins "*"

# 8. Create GitHub repo BEFORE pushing
# Go to github.com/new first
```

---

## 📊 Tech Stack Summary

| Component | Technology | Version |
|---|---|---|
| Agent Framework | Google ADK | 1.14.0 |
| LLM | Gemini 2.5 Flash via Vertex AI | Latest |
| MCP Server | FastMCP | 2.3.3 |
| MCP Transport | Streamable HTTP | - |
| Stock Data | Yahoo Finance (yfinance) | 0.2.54 |
| HTTP Server | Uvicorn | 0.29.0 |
| Deployment | Google Cloud Run | Serverless |
| Container Build | Google Cloud Build | - |
| Language | Python | 3.12 |

---

## 📚 References

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [yfinance Documentation](https://github.com/ranaroussi/yfinance)
- [MCP Specification](https://modelcontextprotocol.io/)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
