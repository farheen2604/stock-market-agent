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
