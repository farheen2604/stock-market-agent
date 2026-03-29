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
