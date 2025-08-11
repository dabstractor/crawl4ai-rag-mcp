#!/bin/bash

# Crawl4AI MCP Visualizer UI Start Script

echo "🚀 Starting Crawl4AI MCP Visualizer UI..."
echo "========================================"

# Check if Node.js is installed
if ! command -v node &> /dev/null
then
    echo "❌ Node.js is not installed. Please install Node.js v14 or higher."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null
then
    echo "❌ npm is not installed. Please install npm v6 or higher."
    exit 1
fi

# Check if dependencies are installed
if [ ! -d "node_modules" ]
then
    echo "⚠️  Node modules not found. Installing dependencies..."
    npm install
    if [ $? -ne 0 ]
    then
        echo "❌ Failed to install dependencies."
        exit 1
    fi
fi

# Check if .env file exists
if [ ! -f ".env" ]
then
    echo "⚠️  .env file not found. Creating from .env.example..."
    if [ -f ".env.example" ]
    then
        cp .env.example .env
        echo "✅ Created .env file from .env.example"
    else
        echo "⚠️  .env.example not found. Creating default .env file..."
        echo "REACT_APP_MCP_SERVER_URL=http://localhost:8051/sse" > .env
        echo "REACT_APP_API_TIMEOUT=30000" >> .env
        echo "REACT_APP_DEFAULT_MATCH_COUNT=10" >> .env
        echo "REACT_APP_PORT=3000" >> .env
    fi
fi

echo "✅ Environment check complete"
echo "🚀 Starting development server..."
echo "🌐 UI will be available at http://localhost:3000"
echo "🔌 Ensure Crawl4AI MCP server is running at http://localhost:8051"
echo "========================================"

# Start the development server
npm start