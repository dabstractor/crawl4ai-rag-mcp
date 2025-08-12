# Crawl4AI MCP HTTP API Endpoints Documentation

## Overview
This document describes the HTTP REST API endpoints implemented for the Crawl4AI MCP server. These endpoints provide browser-compatible access to the MCP server functionality, allowing web-based clients to interact with the server without requiring MCP protocol support.

## Implemented Endpoints

### 1. Health Check Endpoint
**GET /api/health**

Returns the health status of the server and MCP connectivity.

**Response Format:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "mcp_connected": true,
    "uptime_seconds": 120,
    "memory_usage_mb": 45.5
  },
  "message": "Service is healthy"
}
```

### 2. Sources Endpoint
**GET /api/sources**

Returns a list of all available data sources in the database.

**Response Format:**
```json
{
  "success": true,
  "data": [
    {
      "source_id": "example.com",
      "name": "Example Website",
      "url": "https://example.com",
      "document_count": 150,
      "last_updated": "2025-08-12T10:30:00Z",
      "metadata": {}
    }
  ],
  "message": "Successfully retrieved 1 sources"
}
```

### 3. Search/RAG Query Endpoint
**GET /api/search**

Performs semantic search using RAG functionality across crawled documents.

**Query Parameters:**
- `query` (required): Search query string
- `source` (optional): Filter results by source
- `match_count` (optional, default=5): Number of results to return (1-50)

**Response Format:**
```json
{
  "success": true,
  "query": "example search query",
  "total_results": 3,
  "data": [
    {
      "id": "result_1",
      "title": "Example Document Title",
      "content": "Document content excerpt...",
      "url": "https://example.com/page",
      "source_id": "example.com",
      "relevance_score": 0.85,
      "metadata": {},
      "snippet_start": 100,
      "snippet_end": 200
    }
  ],
  "message": "Search completed successfully. Found 3 results."
}
```

### 4. Code Examples Search Endpoint
**GET /api/code-examples**

Searches for code examples relevant to the query.

**Query Parameters:**
- `query` (required): Code search query
- `source_id` (optional): Filter by source ID
- `match_count` (optional, default=5): Number of results to return (1-50)

**Response Format:**
```json
{
  "success": true,
  "query": "python web scraping example",
  "total_results": 2,
  "data": [
    {
      "id": "code_1",
      "title": "web_scraper.py",
      "content": "def scrape_website(url):\n    # Example code content",
      "url": "https://github.com/example/repo/blob/main/web_scraper.py",
      "source_id": "github.com/example/repo",
      "relevance_score": 0.92,
      "metadata": {
        "language": "python",
        "file_path": "web_scraper.py",
        "function_name": "scrape_website"
      },
      "snippet_start": 0,
      "snippet_end": 50
    }
  ],
  "message": "Code examples search completed successfully. Found 2 results."
}
```

## Technical Implementation

### Response Models
All endpoints return standardized response objects:
- `APIResponse`: Base response model
- `HealthResponse`: Health check response
- `SourcesResponse`: Sources list response
- `SearchResponse`: Search results response

### Error Handling
All endpoints include comprehensive error handling with:
- Proper HTTP status codes
- Detailed error messages
- Logging of failures
- Graceful degradation

### Security Features
- CORS middleware for cross-origin requests
- Input validation and sanitization
- Rate limiting (planned)
- Input validation parameters

### Performance Features
- Timeout handling for long-running operations
- Asynchronous processing
- Connection pooling
- Response caching (planned)

## Integration Status

### Completed Components:
- ✅ Response models and formatters
- ✅ Error handling framework
- ✅ HTTP utility functions
- ✅ Health check endpoint
- ✅ Sources endpoint
- ✅ Search/RAG query endpoint
- ✅ Code examples search endpoint
- ✅ CORS middleware
- ✅ Environment configuration
- ✅ Comprehensive logging

### Pending Components:
- ⏳ API endpoint testing and validation
- ⏳ Documentation completion
- ⏳ Response caching implementation
- ⏳ Rate limiting
- ⏳ Input validation and sanitization
- ⏳ Unit tests
- ⏳ Performance monitoring
- ⏳ Docker configuration updates
- ⏳ Final integration testing
- ⏳ API usage examples
- ⏳ Performance optimization

## Deployment Information

### Current Architecture:
The HTTP API endpoints are designed to be integrated with the FastMCP server using the `FastMCP.from_fastapi()` approach, which converts existing FastAPI applications into MCP servers while preserving all HTTP endpoints.

### Service Configuration:
- **Port**: 8051 (configurable via PORT environment variable)
- **Host**: 0.0.0.0 (configurable via HOST environment variable)
- **Base URL**: http://localhost:8051/api/

### Docker Integration:
The HTTP API is integrated into the main MCP Docker service, sharing the same container and port as the MCP protocol endpoints.

## Future Enhancements

### Planned Features:
1. Response caching for improved performance
2. Rate limiting to prevent abuse
3. Enhanced input validation and sanitization
4. Comprehensive unit test coverage
5. Performance monitoring and metrics
6. API usage examples and documentation
7. Benchmarking and optimization
8. Additional endpoints for MCP tool exposure

### Scalability Considerations:
- Connection pooling for database operations
- Asynchronous processing for long-running tasks
- Timeout management for external service calls
- Memory usage optimization
- Load balancing readiness

## Testing and Validation

### Local Testing Commands:
```bash
# Test health endpoint
curl http://localhost:8051/api/health

# Test sources endpoint
curl http://localhost:8051/api/sources

# Test search endpoint
curl "http://localhost:8051/api/search?query=example+search"

# Test code examples endpoint
curl "http://localhost:8051/api/code-examples?query=python+example"
```

### Integration Testing:
The endpoints have been designed to work seamlessly with the existing MCP tools while providing HTTP REST compatibility for browser-based clients.