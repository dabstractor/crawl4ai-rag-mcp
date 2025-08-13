"""
HTTP API endpoints for Crawl4AI MCP Server.

This module defines FastAPI endpoints that wrap existing MCP tools
to provide HTTP REST API access for browser-based clients.
"""

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
import logging

from .responses import APIResponse, HealthResponse, SourcesResponse, SearchResponse, SourceResponse, SourcesListResponse, SearchResultData

# Configure logger for HTTP API
logger = logging.getLogger("http_api")

# Create API router
router = APIRouter(prefix="/api", tags=["HTTP API"])


class SearchRequest(BaseModel):
    """Request model for search endpoint."""
    query: str = Field(..., description="Search query")
    source: Optional[str] = Field(None, description="Filter by source")
    match_count: int = Field(5, description="Number of results to return", ge=1, le=50)


# Import HealthData from responses module
from .responses import HealthData


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    """
    Health check endpoint to verify server status and connectivity.
    
    Returns:
        HealthResponse: Service health status and connectivity information
    """
    try:
        logger.info("Health check requested")
        
        # Import utility functions for server stats
        from ..utils.http_helpers import get_server_stats
        
        # Get server statistics
        stats = get_server_stats()
        
        # Check actual MCP server connectivity by calling a simple tool
        mcp_connected = False
        mcp_tools_available = False
        
        try:
            # Import the global MCP instance
            from ..crawl4ai_mcp import mcp
            
            # Test basic MCP connectivity
            if hasattr(mcp, 'tools') and hasattr(mcp.tools, 'get_available_sources'):
                mcp_connected = True
                mcp_tools_available = True
                logger.info("MCP server connectivity verified")
            else:
                logger.warning("MCP server tools not available")
        except Exception as mcp_error:
            logger.error(f"MCP connectivity check failed: {mcp_error}")
            mcp_connected = False
            mcp_tools_available = False
        
        # Create health check data
        health_status = "healthy" if mcp_connected and mcp_tools_available else "unhealthy"
        health_data = HealthData(
            status=health_status,
            version="1.0.0",
            mcp_connected=mcp_connected,
            uptime_seconds=stats.get("uptime_seconds", 0),
            memory_usage_mb=stats.get("memory_usage_mb", 0.0)
        )
        
        logger.info(f"Health check completed: status={health_status}, mcp_connected={mcp_connected}")
        
        return HealthResponse(
            success=mcp_connected and mcp_tools_available,
            data=health_data,
            message="Service is healthy" if mcp_connected and mcp_tools_available else "Service is unhealthy - MCP not available"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return HealthResponse(
            success=False,
            error=f"Health check failed: {str(e)}",
            data=HealthData(
                status="unhealthy",
                version="1.0.0",
                mcp_connected=False
            )
        )


@router.get("/sources", response_model=SourcesListResponse)
async def get_sources():
    """Get available sources from crawl database"""
    try:
        # Import utility functions
        from ..utils.http_helpers import async_with_timeout
        
        # Import the global MCP instance
        from ..crawl4ai_mcp import mcp
        
        # Call MCP tool to get sources
        raw_sources = await async_with_timeout(mcp.tools.get_available_sources())
        
        # Format response
        sources = []
        for source in raw_sources:
            sources.append(SourceResponse(
                domain=source.get("domain"),
                count=source.get("count", 0),
                last_updated=source.get("last_updated"),
                description=source.get("description")
            ))
            
        return SourcesListResponse(sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve sources: {str(e)}")


@router.get("/search", response_model=SearchResponse)
async def search_documents(
    request: Request,
    query: str = Query(..., description="Search query"),
    source: Optional[str] = Query(None, description="Filter by source"),
    match_count: int = Query(5, description="Number of results", ge=1, le=50)
) -> SearchResponse:
    """
    Perform semantic search using RAG functionality.
    
    Args:
        query: Search query string
        source: Optional source filter
        match_count: Maximum number of results to return
        
    Returns:
        SearchResponse: Search results with metadata
    """
    try:
        logger.info(f"Search requested: query='{query}', source='{source}', match_count={match_count}")
        
        # Validate query parameters
        from ..utils.http_helpers import validate_query_params
        validation_result = validate_query_params(query, match_count, source)
        if not validation_result["valid"]:
            raise ValueError("; ".join(validation_result["errors"]))
        
        # Import utility functions
        from ..utils.http_helpers import async_with_timeout, parse_mcp_response
        from ..utils.http_helpers import format_search_results as format_search_data
        
        # Import the global MCP instance
        from ..crawl4ai_mcp import mcp
        
        # Validate and prepare parameters
        params = validation_result["params"]
        
        # Call MCP tool to perform RAG search
        logger.info(f"Calling perform_rag_query MCP tool with query: {params['query']}")
        mcp_response = await async_with_timeout(
            mcp.tools.perform_rag_query(
                query=params["query"],
                source=params["source"],
                match_count=params["match_count"]
            ),
            timeout_seconds=60.0  # Longer timeout for search operations
        )
        
        # Parse the MCP response
        parsed_response = parse_mcp_response(mcp_response)
        
        # Handle different response types
        if parsed_response.get("type") == "error":
            raise Exception(f"MCP tool error: {parsed_response.get('error')}")
        
        # Extract search results from response
        search_results = []
        if "data" in parsed_response:
            search_results = parsed_response["data"]
        elif "content" in parsed_response and isinstance(parsed_response["content"], (list, dict)):
            search_results = parsed_response["content"] if isinstance(parsed_response["content"], list) else [parsed_response["content"]]
        else:
            # Try to parse as JSON if it's a string
            import json
            try:
                if isinstance(mcp_response, str):
                    search_results = json.loads(mcp_response)
                else:
                    search_results = mcp_response if isinstance(mcp_response, list) else [mcp_response]
            except json.JSONDecodeError:
                search_results = [{"raw_response": str(mcp_response)}]
        
        # Convert to SearchResultData objects
        formatted_results = []
        if isinstance(search_results, list):
            for i, item in enumerate(search_results):
                if isinstance(item, dict):
                    result_data = SearchResultData(
                        id=item.get("id", f"result_{i}"),
                        title=item.get("title", item.get("source_id", "Search Result")),
                        content=item.get("content", "")[:5000],  # Respect max_length
                        url=item.get("url"),
                        source_id=item.get("source_id", item.get("source")),
                        relevance_score=float(item.get("relevance_score", item.get("score", 0.0))),
                        metadata=item.get("metadata", {}),
                        snippet_start=item.get("snippet_start"),
                        snippet_end=item.get("snippet_end")
                    )
                    formatted_results.append(result_data)
        elif isinstance(search_results, dict):
            # Single result object
            result_data = SearchResultData(
                id=search_results.get("id", "result_0"),
                title=search_results.get("title", search_results.get("source_id", "Search Result")),
                content=search_results.get("content", "")[:5000],  # Respect max_length
                url=search_results.get("url"),
                source_id=search_results.get("source_id", search_results.get("source")),
                relevance_score=float(search_results.get("relevance_score", search_results.get("score", 0.0))),
                metadata=search_results.get("metadata", {}),
                snippet_start=search_results.get("snippet_start"),
                snippet_end=search_results.get("snippet_end")
            )
            formatted_results.append(result_data)
        
        logger.info(f"Search completed: found {len(formatted_results)} results")
        
        response = SearchResponse(
            success=True,
            data=formatted_results,
            message=f"Search completed successfully. Found {len(formatted_results)} results."
        )
        response.query = params["query"]
        response.total_results = len(formatted_results)
        
        return response
        
    except ValueError as e:
        logger.error(f"Search parameter validation failed: {e}")
        return SearchResponse(
            success=False,
            error=f"Invalid search parameters: {str(e)}",
            data=[]
        )
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        return SearchResponse(
            success=False,
            error=f"Search failed: {str(e)}",
            data=[]
        )


@router.post("/search", response_model=SearchResponse)
async def search_documents_post(
    request: Request,
    search_request: SearchRequest
) -> SearchResponse:
    """
    Perform semantic search using RAG functionality (POST method).
    
    Args:
        search_request: Search request with query, source filter, and match count
        
    Returns:
        SearchResponse: Search results with metadata
    """
    try:
        logger.info(f"POST Search requested: query='{search_request.query}', source='{search_request.source}', match_count={search_request.match_count}")
        
        # Validate query parameters
        from ..utils.http_helpers import validate_query_params
        validation_result = validate_query_params(search_request.query, search_request.match_count, search_request.source)
        if not validation_result["valid"]:
            raise ValueError("; ".join(validation_result["errors"]))
        
        # Import utility functions
        from ..utils.http_helpers import async_with_timeout, parse_mcp_response
        
        # Import the global MCP instance
        from ..crawl4ai_mcp import mcp
        
        # Validate and prepare parameters
        params = validation_result["params"]
        
        # Call MCP tool to perform RAG search
        logger.info(f"Calling perform_rag_query MCP tool with query: {params['query']}")
        mcp_response = await async_with_timeout(
            mcp.tools.perform_rag_query(
                query=params["query"],
                source=params["source"],
                match_count=params["match_count"]
            ),
            timeout_seconds=60.0  # Longer timeout for search operations
        )
        
        # Parse the MCP response
        parsed_response = parse_mcp_response(mcp_response)
        
        # Handle different response types
        if parsed_response.get("type") == "error":
            raise Exception(f"MCP tool error: {parsed_response.get('error')}")
        
        # Extract search results from response
        search_results = []
        if "data" in parsed_response:
            search_results = parsed_response["data"]
        elif "content" in parsed_response and isinstance(parsed_response["content"], (list, dict)):
            search_results = parsed_response["content"] if isinstance(parsed_response["content"], list) else [parsed_response["content"]]
        else:
            # Try to parse as JSON if it's a string
            import json
            try:
                if isinstance(mcp_response, str):
                    search_results = json.loads(mcp_response)
                else:
                    search_results = mcp_response if isinstance(mcp_response, list) else [mcp_response]
            except json.JSONDecodeError:
                search_results = [{"raw_response": str(mcp_response)}]
        
        # Convert to SearchResultData objects
        formatted_results = []
        if isinstance(search_results, list):
            for i, item in enumerate(search_results):
                if isinstance(item, dict):
                    result_data = SearchResultData(
                        id=item.get("id", f"result_{i}"),
                        title=item.get("title", item.get("source_id", "Search Result")),
                        content=item.get("content", "")[:5000],  # Respect max_length
                        url=item.get("url"),
                        source_id=item.get("source_id", item.get("source")),
                        relevance_score=float(item.get("relevance_score", item.get("score", 0.0))),
                        metadata=item.get("metadata", {}),
                        snippet_start=item.get("snippet_start"),
                        snippet_end=item.get("snippet_end")
                    )
                    formatted_results.append(result_data)
        elif isinstance(search_results, dict):
            # Single result object
            result_data = SearchResultData(
                id=search_results.get("id", "result_0"),
                title=search_results.get("title", search_results.get("source_id", "Search Result")),
                content=search_results.get("content", "")[:5000],  # Respect max_length
                url=search_results.get("url"),
                source_id=search_results.get("source_id", search_results.get("source")),
                relevance_score=float(search_results.get("relevance_score", search_results.get("score", 0.0))),
                metadata=search_results.get("metadata", {}),
                snippet_start=search_results.get("snippet_start"),
                snippet_end=search_results.get("snippet_end")
            )
            formatted_results.append(result_data)
        
        logger.info(f"POST Search completed: found {len(formatted_results)} results")
        
        response = SearchResponse(
            success=True,
            data=formatted_results,
            message=f"Search completed successfully. Found {len(formatted_results)} results."
        )
        response.query = params["query"]
        response.total_results = len(formatted_results)
        
        return response
        
    except ValueError as e:
        logger.error(f"POST Search parameter validation failed: {e}")
        return SearchResponse(
            success=False,
            error=f"Invalid search parameters: {str(e)}",
            data=[]
        )
    except Exception as e:
        logger.error(f"POST Search failed: {e}", exc_info=True)
        return SearchResponse(
            success=False,
            error=f"Search failed: {str(e)}",
            data=[]
        )


@router.get("/code-examples", response_model=SearchResponse)
async def search_code_examples(
    request: Request,
    query: str = Query(..., description="Code search query"),
    source_id: Optional[str] = Query(None, description="Filter by source ID"),
    match_count: int = Query(5, description="Number of results", ge=1, le=50)
) -> SearchResponse:
    """
    Search for code examples relevant to the query.
    
    Args:
        query: Code search query string
        source_id: Optional source ID filter
        match_count: Maximum number of results to return
        
    Returns:
        SearchResponse: Code example search results
    """
    try:
        logger.info(f"Code examples search: query='{query}', source_id='{source_id}', match_count={match_count}")
        
        # Validate query parameters
        from ..utils.http_helpers import validate_query_params
        validation_result = validate_query_params(query, match_count, source_id)
        if not validation_result["valid"]:
            raise ValueError("; ".join(validation_result["errors"]))
        
        # Import utility functions
        from ..utils.http_helpers import async_with_timeout, parse_mcp_response
        
        # Import the global MCP instance
        from ..crawl4ai_mcp import mcp
        
        # Validate and prepare parameters
        params = validation_result["params"]
        
        # Call MCP tool to search for code examples
        logger.info(f"Calling search_code_examples MCP tool with query: {params['query']}")
        mcp_response = await async_with_timeout(
            mcp.tools.search_code_examples(
                query=params["query"],
                source_id=params["source"],
                match_count=params["match_count"]
            ),
            timeout_seconds=60.0  # Longer timeout for search operations
        )
        
        # Parse the MCP response
        parsed_response = parse_mcp_response(mcp_response)
        
        # Handle different response types
        if parsed_response.get("type") == "error":
            raise Exception(f"MCP tool error: {parsed_response.get('error')}")
        
        # Extract code examples from response
        code_examples = []
        if "data" in parsed_response:
            code_examples = parsed_response["data"]
        elif "content" in parsed_response and isinstance(parsed_response["content"], (list, dict)):
            code_examples = parsed_response["content"] if isinstance(parsed_response["content"], list) else [parsed_response["content"]]
        else:
            # Try to parse as JSON if it's a string
            import json
            try:
                if isinstance(mcp_response, str):
                    code_examples = json.loads(mcp_response)
                else:
                    code_examples = mcp_response if isinstance(mcp_response, list) else [mcp_response]
            except json.JSONDecodeError:
                code_examples = [{"raw_response": str(mcp_response)}]
        
        # Convert to SearchResultData objects (reusing the same model for code examples)
        formatted_results = []
        if isinstance(code_examples, list):
            for i, item in enumerate(code_examples):
                if isinstance(item, dict):
                    result_data = SearchResultData(
                        id=item.get("id", f"code_{i}"),
                        title=item.get("title", item.get("file_path", "Code Example")),
                        content=item.get("content", item.get("code", ""))[:5000],  # Respect max_length
                        url=item.get("url"),
                        source_id=item.get("source_id", item.get("source")),
                        relevance_score=float(item.get("relevance_score", item.get("score", 0.0))),
                        metadata=item.get("metadata", {
                            "language": item.get("language"),
                            "file_path": item.get("file_path"),
                            "function_name": item.get("function_name"),
                            "class_name": item.get("class_name")
                        }),
                        snippet_start=item.get("snippet_start"),
                        snippet_end=item.get("snippet_end")
                    )
                    formatted_results.append(result_data)
        elif isinstance(code_examples, dict):
            # Single result object
            result_data = SearchResultData(
                id=code_examples.get("id", "code_0"),
                title=code_examples.get("title", code_examples.get("file_path", "Code Example")),
                content=code_examples.get("content", code_examples.get("code", ""))[:5000],  # Respect max_length
                url=code_examples.get("url"),
                source_id=code_examples.get("source_id", code_examples.get("source")),
                relevance_score=float(code_examples.get("relevance_score", code_examples.get("score", 0.0))),
                metadata=code_examples.get("metadata", {
                    "language": code_examples.get("language"),
                    "file_path": code_examples.get("file_path"),
                    "function_name": code_examples.get("function_name"),
                    "class_name": code_examples.get("class_name")
                }),
                snippet_start=code_examples.get("snippet_start"),
                snippet_end=code_examples.get("snippet_end")
            )
            formatted_results.append(result_data)
        
        logger.info(f"Code examples search completed: found {len(formatted_results)} results")
        
        response = SearchResponse(
            success=True,
            data=formatted_results,
            message=f"Code examples search completed successfully. Found {len(formatted_results)} results."
        )
        response.query = params["query"]
        response.total_results = len(formatted_results)
        
        return response
        
    except ValueError as e:
        logger.error(f"Code examples search parameter validation failed: {e}")
        return SearchResponse(
            success=False,
            error=f"Invalid search parameters: {str(e)}",
            data=[]
        )
    except Exception as e:
        logger.error(f"Code examples search failed: {e}", exc_info=True)
        return SearchResponse(
            success=False,
            error=f"Code examples search failed: {str(e)}",
            data=[]
        )


# Additional utility endpoints

@router.get("/status")
async def get_api_status(request: Request) -> Dict[str, Any]:
    """
    Get detailed API status information.
    
    Returns:
        Dict containing API status, endpoints, and configuration
    """
    return {
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


