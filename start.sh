#!/bin/bash
# Self-Contained Crawl4AI RAG MCP Server Startup Script

echo "🚀 Starting Self-Contained Crawl4AI RAG MCP Server"
echo "=================================================="
echo

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✅ Docker is running"

# Check if .env file exists and has OpenAI API key
if [ ! -f .env ]; then
    echo "❌ .env file not found."
    exit 1
fi

source .env

if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
    echo "❌ OPENAI_API_KEY is not set in .env file"
    echo "Please edit .env and add your OpenAI API key from: https://platform.openai.com/api-keys"
    exit 1
fi

echo "✅ OpenAI API key is configured"

# Stop any existing containers
echo "🧹 Stopping any existing containers..."
docker-compose down --remove-orphans 2>/dev/null || true

# Start the services
echo "🚀 Starting all services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "📊 Service Status:"
docker-compose ps

echo
echo "🎉 Self-Contained Crawl4AI RAG MCP Server is starting up!"
echo
echo "📋 Service URLs:"
echo "   - MCP Server: http://localhost:8051/sse"
echo "   - SearXNG: http://localhost:8080"
echo "   - PostgreSQL: localhost:54321 (internal use only)"
echo
echo "🔧 Claude Code MCP Configuration:"
echo "   claude mcp add-json crawl4ai-rag '{\"type\":\"http\",\"url\":\"http://localhost:8051/sse\"}' --scope user"
echo
echo "📝 To stop the services:"
echo "   docker-compose down"
echo
echo "📊 To view logs:"
echo "   docker-compose logs -f"
echo
echo "🔍 To check status:"
echo "   docker-compose ps"
