#!/bin/bash
# Stop Self-Contained Crawl4AI RAG MCP Server

echo "🛑 Stopping Self-Contained Crawl4AI RAG MCP Server"
echo "================================================"

docker-compose down --remove-orphans

echo "✅ All services stopped"
echo
echo "💾 Data is preserved in Docker volumes"
echo "   To remove all data: docker-compose down -v"
