
---

### Issue 10 — Yahoo Finance rate limiting on Cloud Run

**Error:**
```
I am unable to fetch the stock data due to a rate limit.
Please try again after some time.
```

**Why it occurred:**
Yahoo Finance via yfinance has no official API — it scrapes Yahoo's
website. Google Cloud Run uses GCP IP ranges which Yahoo Finance
detects as automated/bot traffic and aggressively rate limits.
Works fine on local machine (residential IP) but fails on Cloud Run.

**Fix:**
Switched to Finnhub API — official financial data API with
60 calls/minute on free tier, works reliably from Cloud Run.

Changes made:
- requirements.txt: replaced yfinance with finnhub-python
- mcp_server.py: rewrote data fetching using finnhub.Client
- .env: added FINNHUB_API_KEY
- Cloud Run env vars: added FINNHUB_API_KEY

**How to avoid next time:**
When deploying to Cloud Run, always use official APIs with
proper authentication rather than scraping-based libraries.
Yahoo Finance, Google Finance scrapers all fail on GCP IPs.

### Issue 11 — uvicorn version conflict with google-adk

**Error:**
```
Cannot install requirements.txt because these package versions
have conflicting dependencies.
uvicorn==0.29.0 conflicts with google-adk==1.14.0
which needs uvicorn>=0.34.0
```

**Why it occurred:**
Pinned uvicorn to an old version (0.29.0) that conflicts with
google-adk==1.14.0's minimum requirement of uvicorn>=0.34.0.

**Fix:**
```
# Wrong
uvicorn==0.29.0

# Correct
uvicorn>=0.34.0
```

**How to avoid next time:**
Never pin patch versions of infrastructure packages like uvicorn.
Use >= constraints to allow compatible upgrades.
