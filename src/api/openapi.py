"""
OpenAPI schema generation and Swagger UI integration for Crawl4AI MCP HTTP API.

This module provides OpenAPI 3.0 specification generation and Swagger UI/ReDoc
integration for the Starlette-based HTTP API endpoints.
"""

import json
from typing import Dict, Any, List, Optional
from starlette.responses import JSONResponse, HTMLResponse
from starlette.routing import Route


def get_openapi_schema() -> Dict[str, Any]:
    """
    Generate OpenAPI 3.0 schema for the HTTP API endpoints.
    
    Returns:
        OpenAPI schema dictionary
    """
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Crawl4AI MCP HTTP API",
            "description": "HTTP API bridge for Crawl4AI MCP server providing web crawling, RAG search, and code example discovery",
            "version": "1.0.0",
            "contact": {
                "name": "Crawl4AI MCP API Support",
                "url": "https://github.com/crawl4ai"
            }
        },
        "servers": [
            {
                "url": "/api",
                "description": "HTTP API Server"
            }
        ],
        "paths": {
            "/health": {
                "get": {
                    "summary": "Health Check",
                    "description": "Health check endpoint to verify server status and connectivity. Returns server health information including status, version, uptime, and MCP connectivity.",
                    "operationId": "health_check",
                    "tags": ["System"],
                    "responses": {
                        "200": {
                            "description": "Service is healthy",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/HealthResponse"
                                    },
                                    "example": {
                                        "success": True,
                                        "data": {
                                            "status": "healthy",
                                            "version": "1.0.0",
                                            "mcp_connected": True,
                                            "uptime_seconds": 3600,
                                            "memory_usage_mb": 125.5
                                        },
                                        "message": "Service is healthy"
                                    }
                                }
                            }
                        },
                        "500": {
                            "description": "Service is unhealthy",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/HealthResponse"
                                    },
                                    "example": {
                                        "success": False,
                                        "error": "Health check failed: MCP connection timeout",
                                        "data": {
                                            "status": "unhealthy",
                                            "version": "1.0.0",
                                            "mcp_connected": False,
                                            "uptime_seconds": 0,
                                            "memory_usage_mb": 0.0
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/sources": {
                "get": {
                    "summary": "Get Available Sources",
                    "description": "Retrieve all available data sources from the crawl database. Returns a list of sources with domain information, document counts, and last update timestamps.",
                    "operationId": "get_sources",
                    "tags": ["Data Sources"],
                    "responses": {
                        "200": {
                            "description": "Successfully retrieved sources",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SourcesListResponse"
                                    },
                                    "example": {
                                        "sources": [
                                            {
                                                "domain": "example.com",
                                                "count": 25,
                                                "last_updated": "2025-08-13T21:00:00Z",
                                                "description": "Documentation and examples"
                                            },
                                            {
                                                "domain": "docs.python.org",
                                                "count": 150,
                                                "last_updated": "2025-08-13T20:30:00Z",
                                                "description": "Python official documentation"
                                            }
                                        ]
                                    }
                                }
                            }
                        },
                        "500": {
                            "description": "Failed to retrieve sources",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/search": {
                "get": {
                    "summary": "Search Documents (GET)",
                    "description": "Perform semantic search using RAG (Retrieval-Augmented Generation) functionality. Search through crawled documents and return relevant results with content snippets and relevance scores.",
                    "operationId": "search_documents_get",
                    "tags": ["Search"],
                    "parameters": [
                        {
                            "name": "query",
                            "in": "query",
                            "required": True,
                            "description": "Search query string",
                            "schema": {
                                "type": "string",
                                "minLength": 1,
                                "maxLength": 500
                            },
                            "example": "FastAPI authentication middleware"
                        },
                        {
                            "name": "source",
                            "in": "query",
                            "required": False,
                            "description": "Filter results by source domain",
                            "schema": {
                                "type": "string",
                                "maxLength": 255
                            },
                            "example": "docs.python.org"
                        },
                        {
                            "name": "match_count",
                            "in": "query",
                            "required": False,
                            "description": "Maximum number of results to return",
                            "schema": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 50,
                                "default": 5
                            },
                            "example": 10
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Search completed successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SearchResponse"
                                    },
                                    "example": {
                                        "success": True,
                                        "data": [
                                            {
                                                "id": "result_1",
                                                "title": "FastAPI Authentication Guide",
                                                "content": "FastAPI provides several ways to handle authentication...",
                                                "url": "https://fastapi.tiangolo.com/tutorial/security/",
                                                "source_id": "fastapi.tiangolo.com",
                                                "relevance_score": 0.95,
                                                "metadata": {
                                                    "section": "Security",
                                                    "last_crawled": "2025-08-13T20:00:00Z"
                                                }
                                            }
                                        ],
                                        "query": "FastAPI authentication middleware",
                                        "total_results": 1,
                                        "message": "Search completed successfully. Found 1 results."
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Invalid search parameters",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SearchResponse"
                                    },
                                    "example": {
                                        "success": False,
                                        "error": "Invalid search parameters: Query cannot be empty",
                                        "data": []
                                    }
                                }
                            }
                        },
                        "500": {
                            "description": "Search operation failed",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SearchResponse"
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "summary": "Search Documents (POST)",
                    "description": "Perform semantic search using RAG functionality with request body parameters. Same functionality as GET endpoint but with POST body for complex queries.",
                    "operationId": "search_documents_post",
                    "tags": ["Search"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/SearchRequest"
                                },
                                "example": {
                                    "query": "Python async web crawling examples",
                                    "source": "docs.python.org",
                                    "match_count": 10
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Search completed successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SearchResponse"
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Invalid search parameters",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SearchResponse"
                                    }
                                }
                            }
                        },
                        "500": {
                            "description": "Search operation failed",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SearchResponse"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/code-examples": {
                "get": {
                    "summary": "Search Code Examples",
                    "description": "Search for code examples relevant to the query. Returns code snippets with syntax highlighting information, programming language detection, and relevance scoring.",
                    "operationId": "search_code_examples",
                    "tags": ["Code Examples"],
                    "parameters": [
                        {
                            "name": "query",
                            "in": "query",
                            "required": True,
                            "description": "Code search query",
                            "schema": {
                                "type": "string",
                                "minLength": 1,
                                "maxLength": 500
                            },
                            "example": "async function web scraping"
                        },
                        {
                            "name": "source_id",
                            "in": "query",
                            "required": False,
                            "description": "Filter by source identifier",
                            "schema": {
                                "type": "string",
                                "maxLength": 255
                            },
                            "example": "github.com"
                        },
                        {
                            "name": "match_count",
                            "in": "query",
                            "required": False,
                            "description": "Maximum number of code examples to return",
                            "schema": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 50,
                                "default": 5
                            },
                            "example": 5
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Code examples search completed",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SearchResponse"
                                    },
                                    "example": {
                                        "success": True,
                                        "data": [
                                            {
                                                "id": "code_1",
                                                "title": "async_web_scraper.py",
                                                "content": "async def scrape_website(url):\n    async with aiohttp.ClientSession() as session:\n        async with session.get(url) as response:\n            return await response.text()",
                                                "url": "https://github.com/example/crawler",
                                                "source_id": "github.com",
                                                "relevance_score": 0.89,
                                                "metadata": {
                                                    "language": "python",
                                                    "file_path": "src/scraper.py",
                                                    "function_name": "scrape_website"
                                                }
                                            }
                                        ],
                                        "query": "async function web scraping",
                                        "total_results": 1,
                                        "message": "Code examples search completed successfully. Found 1 results."
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Invalid search parameters",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SearchResponse"
                                    }
                                }
                            }
                        },
                        "500": {
                            "description": "Code examples search failed",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SearchResponse"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/status": {
                "get": {
                    "summary": "Get API Status",
                    "description": "Get detailed API status information including available endpoints, configuration, and operational metrics.",
                    "operationId": "get_api_status",
                    "tags": ["System"],
                    "responses": {
                        "200": {
                            "description": "API status information",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/StatusResponse"
                                    },
                                    "example": {
                                        "api_version": "1.0.0",
                                        "status": "operational",
                                        "endpoints": [
                                            "/api/health",
                                            "/api/sources",
                                            "/api/search",
                                            "/api/code-examples",
                                            "/api/status"
                                        ],
                                        "transport": "http",
                                        "cors_enabled": True
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/cache-stats": {
                "get": {
                    "summary": "Get Cache Statistics",
                    "description": "Get cache statistics for all cache instances including hit rates, miss rates, and cache sizes.",
                    "operationId": "get_cache_stats",
                    "tags": ["System"],
                    "responses": {
                        "200": {
                            "description": "Cache statistics",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/CacheStatsResponse"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/cache-clear": {
                "post": {
                    "summary": "Clear All Caches",
                    "description": "Clear all cache instances to force fresh data retrieval on subsequent requests.",
                    "operationId": "clear_cache",
                    "tags": ["System"],
                    "responses": {
                        "200": {
                            "description": "Caches cleared successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean",
                                                "example": True
                                            },
                                            "message": {
                                                "type": "string",
                                                "example": "All caches cleared successfully"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "HealthData": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "Service status",
                            "enum": ["healthy", "unhealthy"],
                            "example": "healthy"
                        },
                        "version": {
                            "type": "string",
                            "description": "API version",
                            "example": "1.0.0"
                        },
                        "mcp_connected": {
                            "type": "boolean",
                            "description": "MCP server connection status",
                            "example": True
                        },
                        "uptime_seconds": {
                            "type": "number",
                            "format": "float",
                            "description": "Server uptime in seconds",
                            "example": 3600.5
                        },
                        "memory_usage_mb": {
                            "type": "number",
                            "format": "float",
                            "description": "Memory usage in MB",
                            "example": 125.7
                        }
                    },
                    "required": ["status", "version", "mcp_connected"]
                },
                "HealthResponse": {
                    "type": "object",
                    "properties": {
                        "success": {
                            "type": "boolean",
                            "description": "Whether the request was successful",
                            "example": True
                        },
                        "data": {
                            "$ref": "#/components/schemas/HealthData"
                        },
                        "error": {
                            "type": "string",
                            "nullable": True,
                            "description": "Error message if request failed",
                            "example": None
                        },
                        "message": {
                            "type": "string",
                            "nullable": True,
                            "description": "Additional message or context",
                            "example": "Service is healthy"
                        }
                    },
                    "required": ["success"]
                },
                "SourceResponse": {
                    "type": "object",
                    "properties": {
                        "domain": {
                            "type": "string",
                            "description": "Source domain",
                            "minLength": 1,
                            "maxLength": 255,
                            "example": "docs.python.org"
                        },
                        "count": {
                            "type": "integer",
                            "description": "Document count",
                            "minimum": 0,
                            "example": 150
                        },
                        "last_updated": {
                            "type": "string",
                            "format": "date-time",
                            "nullable": True,
                            "description": "Last update timestamp",
                            "example": "2025-08-13T20:30:00Z"
                        },
                        "description": {
                            "type": "string",
                            "nullable": True,
                            "description": "Source description",
                            "maxLength": 1000,
                            "example": "Python official documentation"
                        }
                    },
                    "required": ["domain", "count"]
                },
                "SourcesListResponse": {
                    "type": "object",
                    "properties": {
                        "sources": {
                            "type": "array",
                            "items": {
                                "$ref": "#/components/schemas/SourceResponse"
                            },
                            "description": "List of available sources"
                        }
                    },
                    "required": ["sources"]
                },
                "SearchRequest": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query string",
                            "minLength": 1,
                            "maxLength": 500,
                            "example": "FastAPI authentication middleware"
                        },
                        "source": {
                            "type": "string",
                            "nullable": True,
                            "description": "Filter by source domain",
                            "maxLength": 255,
                            "example": "fastapi.tiangolo.com"
                        },
                        "match_count": {
                            "type": "integer",
                            "description": "Number of results to return",
                            "minimum": 1,
                            "maximum": 50,
                            "default": 5,
                            "example": 10
                        }
                    },
                    "required": ["query"]
                },
                "SearchResultData": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": "Unique result identifier",
                            "minLength": 1,
                            "example": "result_1"
                        },
                        "title": {
                            "type": "string",
                            "description": "Result title",
                            "maxLength": 500,
                            "example": "FastAPI Authentication Guide"
                        },
                        "content": {
                            "type": "string",
                            "description": "Result content/excerpt",
                            "maxLength": 5000,
                            "example": "FastAPI provides several ways to handle authentication including OAuth2, JWT tokens, and API keys..."
                        },
                        "url": {
                            "type": "string",
                            "nullable": True,
                            "description": "Source URL",
                            "maxLength": 2000,
                            "example": "https://fastapi.tiangolo.com/tutorial/security/"
                        },
                        "source_id": {
                            "type": "string",
                            "nullable": True,
                            "description": "Source identifier",
                            "maxLength": 255,
                            "example": "fastapi.tiangolo.com"
                        },
                        "relevance_score": {
                            "type": "number",
                            "format": "float",
                            "description": "Relevance score (0.0 to 1.0)",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "example": 0.95
                        },
                        "metadata": {
                            "type": "object",
                            "nullable": True,
                            "description": "Additional result metadata",
                            "example": {
                                "section": "Security",
                                "language": "python",
                                "last_crawled": "2025-08-13T20:00:00Z"
                            }
                        },
                        "snippet_start": {
                            "type": "integer",
                            "nullable": True,
                            "description": "Start position of content snippet",
                            "minimum": 0,
                            "example": 150
                        },
                        "snippet_end": {
                            "type": "integer",
                            "nullable": True,
                            "description": "End position of content snippet",
                            "minimum": 0,
                            "example": 300
                        }
                    },
                    "required": ["id", "title", "content", "relevance_score"]
                },
                "SearchResponse": {
                    "type": "object",
                    "properties": {
                        "success": {
                            "type": "boolean",
                            "description": "Whether the request was successful",
                            "example": True
                        },
                        "data": {
                            "type": "array",
                            "items": {
                                "$ref": "#/components/schemas/SearchResultData"
                            },
                            "description": "Search results"
                        },
                        "error": {
                            "type": "string",
                            "nullable": True,
                            "description": "Error message if request failed"
                        },
                        "message": {
                            "type": "string",
                            "nullable": True,
                            "description": "Additional message or context",
                            "example": "Search completed successfully. Found 5 results."
                        },
                        "query": {
                            "type": "string",
                            "nullable": True,
                            "description": "Original search query",
                            "example": "FastAPI authentication middleware"
                        },
                        "total_results": {
                            "type": "integer",
                            "nullable": True,
                            "description": "Total number of results found",
                            "example": 5
                        },
                        "search_time_ms": {
                            "type": "number",
                            "format": "float",
                            "nullable": True,
                            "description": "Search execution time in milliseconds",
                            "example": 245.7
                        }
                    },
                    "required": ["success", "data"]
                },
                "StatusResponse": {
                    "type": "object",
                    "properties": {
                        "api_version": {
                            "type": "string",
                            "description": "API version",
                            "example": "1.0.0"
                        },
                        "status": {
                            "type": "string",
                            "description": "API operational status",
                            "example": "operational"
                        },
                        "endpoints": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Available API endpoints"
                        },
                        "transport": {
                            "type": "string",
                            "description": "Transport protocol",
                            "example": "http"
                        },
                        "cors_enabled": {
                            "type": "boolean",
                            "description": "Whether CORS is enabled",
                            "example": True
                        }
                    },
                    "required": ["api_version", "status", "endpoints"]
                },
                "CacheStatsResponse": {
                    "type": "object",
                    "properties": {
                        "sources_cache": {
                            "type": "object",
                            "description": "Sources cache statistics"
                        },
                        "health_cache": {
                            "type": "object",
                            "description": "Health cache statistics"
                        },
                        "search_cache": {
                            "type": "object",
                            "description": "Search cache statistics"
                        }
                    }
                },
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "success": {
                            "type": "boolean",
                            "example": False
                        },
                        "error": {
                            "type": "string",
                            "description": "Error message",
                            "example": "Operation failed"
                        },
                        "data": {
                            "nullable": True,
                            "description": "Response data (null for errors)"
                        },
                        "error_code": {
                            "type": "string",
                            "nullable": True,
                            "description": "Specific error code"
                        },
                        "error_details": {
                            "type": "object",
                            "nullable": True,
                            "description": "Additional error details"
                        }
                    },
                    "required": ["success", "error"]
                }
            }
        },
        "tags": [
            {
                "name": "System",
                "description": "System health, status, and cache management endpoints"
            },
            {
                "name": "Data Sources",
                "description": "Endpoints for retrieving available data sources and their metadata"
            },
            {
                "name": "Search",
                "description": "Semantic search and RAG query endpoints for finding relevant content"
            },
            {
                "name": "Code Examples",
                "description": "Code example search and discovery endpoints"
            }
        ]
    }


async def openapi_endpoint(request):
    """
    Serve the OpenAPI JSON schema.
    
    Returns:
        JSONResponse containing the OpenAPI schema
    """
    schema = get_openapi_schema()
    return JSONResponse(content=schema)


def get_swagger_ui_html() -> str:
    """
    Generate Swagger UI HTML page.
    
    Returns:
        HTML string for Swagger UI
    """
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Crawl4AI MCP HTTP API - Swagger UI</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.10.3/swagger-ui.css" />
    <link rel="icon" type="image/png" href="https://fastapi.tiangolo.com/img/favicon.png" />
    <style>
        html {
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }
        *, *:before, *:after {
            box-sizing: inherit;
        }
        body {
            margin:0;
            background: #fafafa;
        }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.3/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.3/swagger-ui-standalone-preset.js"></script>
    <script>
        const ui = SwaggerUIBundle({
            url: '/api/openapi.json',
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIStandalonePreset
            ],
            plugins: [
                SwaggerUIBundle.plugins.DownloadUrl
            ],
            layout: "StandaloneLayout",
            defaultModelsExpandDepth: 1,
            defaultModelExpandDepth: 1,
            tryItOutEnabled: true
        });
    </script>
</body>
</html>
"""


def get_redoc_html() -> str:
    """
    Generate ReDoc HTML page.
    
    Returns:
        HTML string for ReDoc
    """
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Crawl4AI MCP HTTP API - ReDoc</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    <link rel="icon" type="image/png" href="https://fastapi.tiangolo.com/img/favicon.png" />
    <style>
        body {
            margin: 0;
            padding: 0;
        }
    </style>
</head>
<body>
    <redoc spec-url="/api/openapi.json"></redoc>
    <script src="https://cdn.redoc.ly/redoc/v2.1.3/bundles/redoc.standalone.js"></script>
</body>
</html>
"""


async def swagger_ui_endpoint(request):
    """
    Serve the Swagger UI HTML page.
    
    Returns:
        HTMLResponse containing Swagger UI
    """
    html_content = get_swagger_ui_html()
    return HTMLResponse(content=html_content, status_code=200)


async def redoc_endpoint(request):
    """
    Serve the ReDoc HTML page.
    
    Returns:
        HTMLResponse containing ReDoc
    """
    html_content = get_redoc_html()
    return HTMLResponse(content=html_content, status_code=200)


def get_documentation_routes() -> List[Route]:
    """
    Get the documentation routes for OpenAPI, Swagger UI, and ReDoc.
    
    Returns:
        List of Route objects for documentation endpoints
    """
    return [
        Route("/api/openapi.json", openapi_endpoint, methods=["GET"]),
        Route("/api/docs", swagger_ui_endpoint, methods=["GET"]),
        Route("/api/redoc", redoc_endpoint, methods=["GET"]),
    ]