"""
Stock Market MCP Server
Exposes live stock data from Finnhub as MCP tools.
"""

import json
import logging
import os
import sys
import uvicorn
import finnhub
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("stock-market-server")

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "d74euv1r01qno4q1h0bgd74euv1r01qno4q1h0c0")
client = finnhub.Client(api_key=FINNHUB_API_KEY)


@mcp.tool()
def get_stock_price(ticker: str) -> str:
    """
    Fetches the current live stock price and key metrics for a given ticker symbol.

    Args:
        ticker: Stock ticker symbol e.g. AAPL, GOOGL, MSFT, TSLA

    Returns:
        JSON string with current price, change, volume and key metrics.
    """
    try:
        ticker = ticker.upper()

        quote = client.quote(ticker)
        profile = client.company_profile2(symbol=ticker)
        metric = client.company_basic_financials(ticker, 'all')

        if not quote or quote.get('c', 0) == 0:
            return json.dumps({
                "error": f"Could not fetch data for ticker '{ticker}'. Please check the symbol."
            })

        current_price = quote.get('c', 'N/A')
        prev_close = quote.get('pc', 'N/A')
        change = quote.get('d', 'N/A')
        change_pct = f"{quote.get('dp', 'N/A')}%"
        day_high = quote.get('h', 'N/A')
        day_low = quote.get('l', 'N/A')

        metrics = metric.get('metric', {})

        result = {
            "ticker": ticker,
            "company_name": profile.get('name', 'N/A'),
            "current_price": current_price,
            "currency": profile.get('currency', 'USD'),
            "previous_close": prev_close,
            "price_change": change,
            "price_change_pct": change_pct,
            "day_high": day_high,
            "day_low": day_low,
            "52_week_high": metrics.get('52WeekHigh', 'N/A'),
            "52_week_low": metrics.get('52WeekLow', 'N/A'),
            "market_cap": profile.get('marketCapitalization', 'N/A'),
            "pe_ratio": metrics.get('peBasicExclExtraTTM', 'N/A'),
            "eps": metrics.get('epsBasicExclExtraItemsTTM', 'N/A'),
            "dividend_yield": metrics.get('dividendYieldIndicatedAnnual', 'N/A'),
            "sector": profile.get('finnhubIndustry', 'N/A'),
            "exchange": profile.get('exchange', 'N/A'),
            "ipo_date": profile.get('ipo', 'N/A'),
            "website": profile.get('weburl', 'N/A'),
        }

        logger.info(f"[MCP] Fetched stock data for {ticker}")
        return json.dumps(result, default=str)

    except Exception as e:
        logger.error(f"[MCP] Error fetching {ticker}: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_stock_summary(ticker: str) -> str:
    """
    Fetches analyst recommendations and price targets for a given stock ticker.

    Args:
        ticker: Stock ticker symbol e.g. AAPL, GOOGL, MSFT, TSLA

    Returns:
        JSON string with analyst recommendations and price targets.
    """
    try:
        ticker = ticker.upper()

        recommendation = client.recommendation_trends(ticker)
        price_target = client.price_target(ticker)
        profile = client.company_profile2(symbol=ticker)
        news = client.company_news(ticker, _from="2024-01-01", to="2025-12-31")

        latest_rec = recommendation[0] if recommendation else {}

        result = {
            "ticker": ticker,
            "company_name": profile.get('name', 'N/A'),
            "analyst_buy": latest_rec.get('buy', 'N/A'),
            "analyst_hold": latest_rec.get('hold', 'N/A'),
            "analyst_sell": latest_rec.get('sell', 'N/A'),
            "analyst_strong_buy": latest_rec.get('strongBuy', 'N/A'),
            "analyst_strong_sell": latest_rec.get('strongSell', 'N/A'),
            "target_high_price": price_target.get('targetHigh', 'N/A'),
            "target_low_price": price_target.get('targetLow', 'N/A'),
            "target_mean_price": price_target.get('targetMean', 'N/A'),
            "target_median_price": price_target.get('targetMedian', 'N/A'),
            "number_of_analysts": price_target.get('lastUpdated', 'N/A'),
            "latest_news_headline": news[0].get('headline', 'N/A') if news else 'N/A',
        }

        logger.info(f"[MCP] Fetched summary for {ticker}")
        return json.dumps(result, default=str)

    except Exception as e:
        logger.error(f"[MCP] Error fetching summary for {ticker}: {e}")
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    logger.info(f"Starting Stock Market MCP Server on port {port}")
    app = mcp.http_app(path="/mcp")
    uvicorn.run(app, host="0.0.0.0", port=port)
