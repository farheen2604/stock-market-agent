#!/bin/bash
python /app/mcp_server.py 5000 &
sleep 5
export MCP_SERVER_URL="http://127.0.0.1:5000/mcp"
export GOOGLE_GENAI_USE_VERTEXAI=1
export GOOGLE_CLOUD_PROJECT=adk-mcp-491318
export GOOGLE_CLOUD_LOCATION=us-central1
export MODEL=gemini-2.5-flash
cd /app
adk web --host 0.0.0.0 --port ${PORT:-8080}
