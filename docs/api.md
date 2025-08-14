# Crawl4AI MCP HTTP API Documentation

## Overview

This API provides HTTP access to the Crawl4AI MCP server functionality, enabling browser-based UI access to web crawling, document search, and code example retrieval capabilities. The API wraps the underlying MCP (Model Context Protocol) tools to provide standard REST endpoints that can be consumed by web applications, mobile apps, or any HTTP client.

## Base URL

```
http://localhost:8051/api
```

## Authentication

Currently, the API does not require authentication. For production deployments, consider implementing API key authentication or OAuth2.

## Response Format

All API endpoints return responses in a consistent format:

```json
{
  "success": true,
  "data": { /* endpoint-specific data */ },
  "message": "Optional descriptive message",
  "error": null
}
```

For errors:

```json
{
  "success": false,
  "data": null,
  "message": null,
  "error": "Error description"
}
```

## Endpoints

### Health Check

**GET `/api/health`**

Checks the health and status of the MCP server, including connectivity and system resources.

**Response:**

```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "mcp_connected": true,
    "uptime_seconds": 3600,
    "memory_usage_mb": 45.5
  },
  "message": "Service is healthy"
}
```

**Response Fields:**
- `status`: Service status (`healthy` or `unhealthy`)
- `version`: API version
- `mcp_connected`: Whether MCP server is connected
- `uptime_seconds`: Server uptime in seconds
- `memory_usage_mb`: Current memory usage in MB

**Example:**

```bash
curl http://localhost:8051/api/health
```

---

### Get Available Sources

**GET `/api/sources`**

Retrieves all available data sources from the crawl database with document counts and metadata.

**Response:**

```json
{
  "sources": [
    {
      "domain": "example.com",
      "count": 150,
      "last_updated": "2025-01-15T10:30:00Z",
      "description": "Documentation site"
    },
    {
      "domain": "github.com/user/repo",
      "count": 75,
      "last_updated": "2025-01-14T15:45:00Z",
      "description": "Code repository"
    }
  ]
}
```

**Response Fields:**
- `domain`: Source domain or identifier
- `count`: Number of documents from this source
- `last_updated`: ISO timestamp of last update
- `description`: Human-readable source description

**Example:**

```bash
curl http://localhost:8051/api/sources
```

---

### Search Content

**GET `/api/search`**

Performs semantic search using RAG (Retrieval-Augmented Generation) functionality across crawled documents.

**Parameters:**
- `query` (required): Search query string
- `source` (optional): Filter by specific source domain
- `match_count` (optional): Number of results to return (default: 5, max: 50)

**Response:**

```json
{
  "success": true,
  "query": "example search query",
  "total_results": 3,
  "data": [
    {
      "id": "result_1",
      "title": "Example Document Title",
      "content": "Document content excerpt with relevant information about the search query...",
      "url": "https://example.com/page",
      "source_id": "example.com",
      "relevance_score": 0.85,
      "metadata": {
        "page_type": "documentation",
        "section": "getting-started"
      },
      "snippet_start": 100,
      "snippet_end": 200
    }
  ],
  "message": "Search completed successfully. Found 3 results."
}
```

**Response Fields:**
- `id`: Unique result identifier
- `title`: Document or page title
- `content`: Text content excerpt (up to 5000 characters)
- `url`: Source URL if available
- `source_id`: Source domain/identifier
- `relevance_score`: Relevance score from 0.0 to 1.0
- `metadata`: Additional context and metadata
- `snippet_start`/`snippet_end`: Content excerpt positions

**Examples:**

```bash
# Basic search
curl "http://localhost:8051/api/search?query=web+scraping"

# Search with source filter
curl "http://localhost:8051/api/search?query=authentication&source=docs.example.com"

# Search with custom result count
curl "http://localhost:8051/api/search?query=API+documentation&match_count=10"
```

---

### Search Content (POST)

**POST `/api/search`**

Alternative POST method for search with request body. Useful for complex queries or when URL length limits are a concern.

**Request Body:**

```json
{
  "query": "search query",
  "source": "optional-source-filter",
  "match_count": 5
}
```

**Response:** Same format as GET `/api/search`

**Example:**

```bash
curl -X POST http://localhost:8051/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning algorithms",
    "source": "research.example.com",
    "match_count": 10
  }'
```

---

### Search Code Examples

**GET `/api/code-examples`**

Searches for code examples relevant to the query across crawled repositories and documentation.

**Parameters:**
- `query` (required): Code search query string
- `source_id` (optional): Filter by specific source ID
- `match_count` (optional): Number of results to return (default: 5, max: 50)

**Response:**

```json
{
  "success": true,
  "query": "python web scraping example",
  "total_results": 2,
  "data": [
    {
      "id": "code_1",
      "title": "web_scraper.py",
      "content": "def scrape_website(url):\n    \"\"\"\n    Scrape a website and extract content.\n    \n    Args:\n        url (str): The URL to scrape\n        \n    Returns:\n        dict: Scraped content\n    \"\"\"\n    import requests\n    from bs4 import BeautifulSoup\n    \n    response = requests.get(url)\n    soup = BeautifulSoup(response.content, 'html.parser')\n    \n    return {\n        'title': soup.title.string if soup.title else '',\n        'content': soup.get_text()\n    }",
      "url": "https://github.com/example/repo/blob/main/web_scraper.py",
      "source_id": "github.com/example/repo",
      "relevance_score": 0.92,
      "metadata": {
        "language": "python",
        "file_path": "src/web_scraper.py",
        "function_name": "scrape_website",
        "class_name": null
      },
      "snippet_start": 0,
      "snippet_end": 50
    }
  ],
  "message": "Code examples search completed successfully. Found 2 results."
}
```

**Response Fields:** Same as search endpoint, with additional metadata:
- `language`: Programming language detected
- `file_path`: Relative path to the code file
- `function_name`: Function name if applicable
- `class_name`: Class name if applicable

**Examples:**

```bash
# Search for Python examples
curl "http://localhost:8051/api/code-examples?query=python+authentication"

# Search in specific repository
curl "http://localhost:8051/api/code-examples?query=JWT+token&source_id=github.com/user/repo"

# Get more results
curl "http://localhost:8051/api/code-examples?query=API+client&match_count=15"
```

---

### API Status

**GET `/api/status`**

Returns detailed API status information including available endpoints and configuration.

**Response:**

```json
{
  "api_version": "1.0.0",
  "status": "operational",
  "endpoints": [
    "/api/health",
    "/api/sources",
    "/api/search",
    "/api/code-examples",
    "/api/status",
    "/api/cache-stats",
    "/api/cache-clear"
  ],
  "transport": "http",
  "cors_enabled": true
}
```

**Example:**

```bash
curl http://localhost:8051/api/status
```

---

### Cache Statistics

**GET `/api/cache-stats`**

Returns caching statistics for performance monitoring.

**Response:**

```json
{
  "sources_cache": {
    "hits": 45,
    "misses": 12,
    "size": 3,
    "ttl_seconds": 300
  },
  "health_cache": {
    "hits": 150,
    "misses": 5,
    "size": 1,
    "ttl_seconds": 60
  },
  "search_cache": {
    "hits": 25,
    "misses": 30,
    "size": 15,
    "ttl_seconds": 180
  }
}
```

**Example:**

```bash
curl http://localhost:8051/api/cache-stats
```

---

### Clear Cache

**POST `/api/cache-clear`**

Clears all API caches. Useful for debugging or forcing fresh data retrieval.

**Response:**

```json
{
  "success": true,
  "message": "All caches cleared successfully"
}
```

**Example:**

```bash
curl -X POST http://localhost:8051/api/cache-clear
```

## Error Handling

The API returns standard HTTP status codes and a consistent error format:

### Common Status Codes

- **200**: Successful operation
- **400**: Bad request (invalid parameters)
- **404**: Endpoint not found
- **429**: Too many requests (rate limiting)
- **500**: Internal server error
- **503**: Service unavailable (MCP tools not responding)

### Error Response Format

```json
{
  "success": false,
  "data": null,
  "error": "Detailed error description",
  "message": null
}
```

### Common Error Examples

**Invalid search parameters:**
```json
{
  "success": false,
  "data": [],
  "error": "Invalid search parameters: Query cannot be empty; Match count must be between 1 and 50"
}
```

**MCP connection error:**
```json
{
  "success": false,
  "data": null,
  "error": "MCP tool error: Connection timeout"
}
```

**Rate limit exceeded:**
```json
{
  "success": false,
  "data": null,
  "error": "Rate limit exceeded. Please try again later."
}
```

## Rate Limiting

The API is rate limited to **60 requests per minute per IP address** by default. Rate limits can be configured via environment variables:

- `API_RATE_LIMIT`: Requests per minute (default: 60)
- `RATE_LIMIT_ENABLED`: Enable/disable rate limiting (default: true)

When rate limits are exceeded, the API returns:
- HTTP status: `429 Too Many Requests`
- `Retry-After` header with seconds to wait

## Performance Considerations

### Caching

Responses are cached to improve performance:
- **Health checks**: 60 seconds
- **Sources**: 5 minutes
- **Search results**: 3 minutes

Cache TTL can be configured via environment variables.

### Timeouts

- Search operations: 60 seconds
- Health checks: 5 seconds
- Source queries: 30 seconds

### Content Limits

- Search result content: Maximum 5,000 characters per result
- Query length: Maximum 1,000 characters
- Results per request: Maximum 50

## CORS Support

Cross-Origin Resource Sharing (CORS) is enabled by default. Configure allowed origins via the `CORS_ORIGINS` environment variable:

```bash
# Allow all origins (development only)
CORS_ORIGINS=*

# Allow specific origins (production)
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

## SDK Examples

### JavaScript/Node.js

```javascript
const API_BASE = 'http://localhost:8051/api';

class Crawl4AIAPI {
  async health() {
    const response = await fetch(`${API_BASE}/health`);
    return await response.json();
  }

  async search(query, options = {}) {
    const params = new URLSearchParams({
      query,
      ...options
    });
    
    const response = await fetch(`${API_BASE}/search?${params}`);
    return await response.json();
  }

  async getSources() {
    const response = await fetch(`${API_BASE}/sources`);
    return await response.json();
  }

  async searchCode(query, options = {}) {
    const params = new URLSearchParams({
      query,
      ...options
    });
    
    const response = await fetch(`${API_BASE}/code-examples?${params}`);
    return await response.json();
  }
}

// Usage example
const api = new Crawl4AIAPI();

// Check health
const health = await api.health();
console.log('API Status:', health.data.status);

// Search documents
const results = await api.search('machine learning', {
  source: 'docs.example.com',
  match_count: 10
});
console.log('Found results:', results.total_results);

// Search code examples
const codeResults = await api.searchCode('python async', {
  match_count: 5
});
console.log('Code examples:', codeResults.data.length);
```

### Python

```python
import requests
from typing import Optional, Dict, Any

class Crawl4AIAPI:
    def __init__(self, base_url: str = "http://localhost:8051/api"):
        self.base_url = base_url
        
    def health(self) -> Dict[str, Any]:
        """Check API health status."""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def search(self, query: str, source: Optional[str] = None, 
               match_count: int = 5) -> Dict[str, Any]:
        """Search documents using RAG."""
        params = {"query": query, "match_count": match_count}
        if source:
            params["source"] = source
            
        response = requests.get(f"{self.base_url}/search", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_sources(self) -> Dict[str, Any]:
        """Get available data sources."""
        response = requests.get(f"{self.base_url}/sources")
        response.raise_for_status()
        return response.json()
    
    def search_code(self, query: str, source_id: Optional[str] = None,
                    match_count: int = 5) -> Dict[str, Any]:
        """Search code examples."""
        params = {"query": query, "match_count": match_count}
        if source_id:
            params["source_id"] = source_id
            
        response = requests.get(f"{self.base_url}/code-examples", params=params)
        response.raise_for_status()
        return response.json()

# Usage example
api = Crawl4AIAPI()

# Check health
health = api.health()
print(f"API Status: {health['data']['status']}")

# Search documents
results = api.search("web scraping best practices", match_count=10)
print(f"Found {results['total_results']} results")

# Search code examples
code_results = api.search_code("async python web scraping")
for result in code_results['data']:
    print(f"Code: {result['title']} (Score: {result['relevance_score']})")
```

### cURL Examples

```bash
#!/bin/bash

# Set base URL
API_BASE="http://localhost:8051/api"

# Health check
echo "=== Health Check ==="
curl -s "$API_BASE/health" | jq '.'

# Get sources
echo -e "\n=== Available Sources ==="
curl -s "$API_BASE/sources" | jq '.sources[]'

# Search documents
echo -e "\n=== Document Search ==="
curl -s "$API_BASE/search?query=machine+learning&match_count=3" | jq '.data[]'

# Search code examples
echo -e "\n=== Code Examples ==="
curl -s "$API_BASE/code-examples?query=python+web+scraping&match_count=2" | jq '.data[]'

# POST search with JSON body
echo -e "\n=== POST Search ==="
curl -s -X POST "$API_BASE/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "API authentication methods",
    "match_count": 5
  }' | jq '.'

# Cache statistics
echo -e "\n=== Cache Stats ==="
curl -s "$API_BASE/cache-stats" | jq '.'
```

## Deployment

For deployment information including Docker setup, environment variables, security considerations, and production configurations, see the [deployment guide](deployment.md).

## Support

For issues, questions, or feature requests:
- Check the health endpoint for system status
- Review server logs for detailed error information
- Verify environment configuration and dependencies
- Test with the provided examples to isolate issues

## Version History

- **v1.0.0**: Initial HTTP API implementation with search, sources, and code examples endpoints
- **v1.0.1**: Added caching, rate limiting, and improved error handling
- **v1.0.2**: Enhanced response models and added comprehensive documentation