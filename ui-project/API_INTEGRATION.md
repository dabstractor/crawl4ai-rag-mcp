# API Integration Guide

This document explains how the Crawl4AI MCP Visualizer UI integrates with the Crawl4AI MCP Server API.

## Overview

The Crawl4AI MCP Server provides a comprehensive set of tools for web crawling, search, and RAG (Retrieval Augmented Generation) capabilities. The server is accessible via HTTP SSE (Server-Sent Events) transport at `http://localhost:8051/sse`.

## Connection Architecture

The UI connects to the MCP server using the SSE transport protocol. This allows for real-time communication between the client and server, with the server pushing updates and responses to the client as events.

### Connection Flow

1. Client establishes SSE connection to `http://localhost:8051/sse`
2. Client sends requests by making HTTP POST calls to the MCP server
3. Server processes requests and sends responses back via SSE events
4. Client listens for relevant events and updates the UI accordingly

## Service Layer Implementation

The integration is handled through the `MCPService` class located at `src/services/mcpService.js`.

### Key Methods

#### `initializeConnection()`
Establishes the initial SSE connection to the MCP server.

#### `sendRequest(toolName, argumentsObj)`
Generic method for sending requests to any MCP tool.

#### `getAvailableSources()`
Calls the `get_available_sources` tool to retrieve information about crawled sources.

#### `performRagQuery(query, source, matchCount)`
Calls the `perform_rag_query` tool for semantic search functionality.

#### `searchCodeExamples(query, sourceId, matchCount)`
Calls the `search_code_examples` tool for code example search (conditional feature).

#### `scrapeUrls(urls, maxConcurrent, batchSize, returnRawMarkdown)`
Calls the `scrape_urls` tool for manual URL scraping.

#### `smartCrawlUrl(url, maxDepth, maxConcurrent, chunkSize, returnRawMarkdown)`
Calls the `smart_crawl_url` tool for intelligent website crawling.

#### `search(query, returnRawMarkdown, numResults, batchSize, maxConcurrent, maxRagWorkers)`
Calls the `search` tool for comprehensive search functionality.

## Available Tools

### Core Tools (Always Available)

1. **`search`** - Comprehensive search tool
2. **`scrape_urls`** - URL scraping tool
3. **`smart_crawl_url`** - Intelligent website crawling
4. **`get_available_sources`** - Source information retrieval
5. **`perform_rag_query`** - Semantic search

### Conditional Tools

1. **`search_code_examples`** - Code example search (requires `USE_AGENTIC_RAG=true`)

### Knowledge Graph Tools

1. **`parse_github_repository`** - GitHub repository parsing
2. **`check_ai_script_hallucinations`** - AI script validation
3. **`query_knowledge_graph`** - Knowledge graph querying

## Implementation Status

### Completed
- Basic service layer structure
- Connection initialization framework
- Generic request sending method
- All tool method stubs

### In Progress
- SSE connection implementation
- Event handling for server responses
- Error handling and retry logic

### Pending
- Full integration with all MCP tools
- Real-time updates and streaming responses
- Authentication handling (if required)

## Error Handling

The service layer includes comprehensive error handling for:
- Connection failures
- Timeout errors
- Invalid responses
- Network issues

## Configuration

The integration can be configured through environment variables:
- `REACT_APP_MCP_SERVER_URL` - MCP server URL (default: `http://localhost:8051/sse`)
- `REACT_APP_API_TIMEOUT` - Request timeout in milliseconds (default: 30000)

## Future Enhancements

1. Implement full SSE connection with proper event handling
2. Add request/response correlation for tracking requests
3. Implement retry logic for failed requests
4. Add connection health monitoring
5. Implement caching for frequently requested data
6. Add support for streaming responses where applicable