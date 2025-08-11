#!/bin/bash

# Crawl4AI MCP + UI Complete Stack Start Script

echo "🚀 Starting Complete Crawl4AI MCP Stack with UI..."
echo "================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null 2>&1; then
    echo "❌ Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env file from .env.example"
        echo "📝 Please edit .env with your API keys before continuing"
        exit 1
    else
        echo "❌ .env.example not found. Cannot proceed without configuration."
        exit 1
    fi
fi

echo "🔧 Building and starting Docker Compose stack..."
echo "This may take a few minutes on first run..."

# Use docker compose (newer) or docker-compose (legacy)
if docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Build and start the stack
$COMPOSE_CMD up -d --build

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Complete Crawl4AI MCP Stack is now running!"
    echo "================================================="
    echo "🔗 MCP Server:        http://localhost:8051"
    echo "🌐 Visualizer UI:     http://localhost:3741"
    echo "🔍 SearXNG (internal): http://localhost:8080"
    echo "📊 PostgreSQL:        localhost:54321"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Visit http://localhost:3741 to use the web interface"
    echo "2. Configure your MCP client to connect to http://localhost:8051/sse"
    echo "3. Check logs with: $COMPOSE_CMD logs -f"
    echo "4. Stop stack with: $COMPOSE_CMD down"
    echo ""
    echo "🛠️  For troubleshooting, check the logs:"
    echo "   $COMPOSE_CMD logs mcp-crawl4ai"
    echo "   $COMPOSE_CMD logs crawl4ai-ui"
    echo "   $COMPOSE_CMD logs postgres"
else
    echo "❌ Failed to start the stack. Check the logs for errors:"
    echo "   $COMPOSE_CMD logs"
    exit 1
fi