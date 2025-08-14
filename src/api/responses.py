"""
Response models for Crawl4AI MCP Server HTTP API.

This module defines Pydantic models for consistent API responses
across all HTTP endpoints.
"""

from pydantic import BaseModel, Field, validator, ConfigDict
from typing import List, Dict, Any, Optional, Union, Generic, TypeVar
from datetime import datetime
import json

# Generic type for response data
T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    """Base response model for all API endpoints."""
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )
    
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[T] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if request failed")
    message: Optional[str] = Field(None, description="Additional message or context")
    # timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")  # Temporarily disabled for JSON serialization


class HealthData(BaseModel):
    """Health check data model."""
    status: str = Field(..., description="Service status (healthy/unhealthy)")
    version: str = Field(..., description="API version")
    mcp_connected: bool = Field(..., description="MCP server connection status")
    uptime_seconds: Optional[float] = Field(None, description="Server uptime in seconds")
    memory_usage_mb: Optional[float] = Field(None, description="Memory usage in MB")


class HealthResponse(APIResponse[HealthData]):
    """Response model for health check endpoint."""
    pass


class SourceData(BaseModel):
    """Data model for a single source."""
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )
    
    source_id: str = Field(..., description="Unique source identifier")
    name: str = Field(..., description="Human-readable source name")
    url: Optional[str] = Field(None, description="Source URL if applicable")
    document_count: int = Field(0, description="Number of documents from this source")
    last_updated: Optional[datetime] = Field(None, description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional source metadata")


class SourceResponse(BaseModel):
    """Individual source response model as specified in Task #4."""
    domain: str = Field(..., description="Source domain", min_length=1, max_length=255)
    count: int = Field(..., description="Document count", ge=0)
    last_updated: Optional[str] = Field(None, description="Last update timestamp")
    description: Optional[str] = Field(None, description="Source description", max_length=1000)
    
    @validator('domain')
    def validate_domain(cls, v):
        """Validate domain format."""
        if not v or not v.strip():
            raise ValueError('Domain cannot be empty')
        return v.strip()


class SourcesListResponse(BaseModel):
    """Sources list response model as specified in Task #4."""
    sources: List[SourceResponse] = Field(..., description="List of sources")


class SourcesResponse(APIResponse[List[SourceData]]):
    """Response model for sources endpoint (extended version)."""
    pass


class SearchResultData(BaseModel):
    """Data model for a single search result."""
    id: str = Field(..., description="Unique result identifier", min_length=1)
    title: str = Field(..., description="Result title", max_length=500)
    content: str = Field(..., description="Result content/excerpt", max_length=5000)
    url: Optional[str] = Field(None, description="Source URL", max_length=2000)
    source_id: Optional[str] = Field(None, description="Source identifier", max_length=255)
    relevance_score: float = Field(..., description="Relevance score (0.0 to 1.0)", ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional result metadata")
    snippet_start: Optional[int] = Field(None, description="Start position of content snippet", ge=0)
    snippet_end: Optional[int] = Field(None, description="End position of content snippet", ge=0)
    
    @validator('snippet_end')
    def validate_snippet_positions(cls, v, values):
        """Validate that snippet_end is greater than snippet_start."""
        if v is not None and 'snippet_start' in values and values['snippet_start'] is not None:
            if v <= values['snippet_start']:
                raise ValueError('snippet_end must be greater than snippet_start')
        return v


class SearchResponse(APIResponse[List[SearchResultData]]):
    """Response model for search endpoints."""
    query: Optional[str] = Field(None, description="Original search query")
    total_results: Optional[int] = Field(None, description="Total number of results found")
    search_time_ms: Optional[float] = Field(None, description="Search execution time in milliseconds")


class CodeExampleData(BaseModel):
    """Data model for code examples."""
    id: str = Field(..., description="Unique code example identifier")
    title: str = Field(..., description="Code example title")
    code: str = Field(..., description="Code content")
    language: str = Field(..., description="Programming language")
    description: Optional[str] = Field(None, description="Code example description")
    url: Optional[str] = Field(None, description="Source URL")
    source_id: Optional[str] = Field(None, description="Source identifier")
    relevance_score: float = Field(..., description="Relevance score (0.0 to 1.0)")
    tags: Optional[List[str]] = Field(None, description="Code example tags")


class CodeExamplesResponse(APIResponse[List[CodeExampleData]]):
    """Response model for code examples endpoint."""
    query: Optional[str] = Field(None, description="Original search query")
    total_results: Optional[int] = Field(None, description="Total number of results found")
    search_time_ms: Optional[float] = Field(None, description="Search execution time in milliseconds")


class ErrorResponse(APIResponse[None]):
    """Response model for error cases."""
    error_code: Optional[str] = Field(None, description="Specific error code")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class PaginationMeta(BaseModel):
    """Pagination metadata for paginated responses."""
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Results per page")
    total_pages: int = Field(..., description="Total number of pages")
    total_results: int = Field(..., description="Total number of results")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


class PaginatedResponse(APIResponse[T]):
    """Response model for paginated endpoints."""
    pagination: PaginationMeta = Field(..., description="Pagination metadata")


# Utility functions for creating responses

def create_success_response(data: T, message: str = None) -> APIResponse[T]:
    """Create a successful API response."""
    return APIResponse(
        success=True,
        data=data,
        message=message
    )


def create_error_response(error: str, data: T = None) -> APIResponse[T]:
    """Create an error API response.""" 
    return APIResponse(
        success=False,
        data=data,
        error=error
    )


def create_health_response(
    status: str = "healthy",
    version: str = "1.0.0",
    mcp_connected: bool = True,
    uptime_seconds: float = None,
    memory_usage_mb: float = None,
    message: str = None
) -> HealthResponse:
    """Create a health check response."""
    return HealthResponse(
        success=True,
        data=HealthData(
            status=status,
            version=version,
            mcp_connected=mcp_connected,
            uptime_seconds=uptime_seconds,
            memory_usage_mb=memory_usage_mb
        ),
        message=message
    )


def create_sources_response(sources: List[SourceData], message: str = None) -> SourcesResponse:
    """Create a sources response."""
    return SourcesResponse(
        success=True,
        data=sources,
        message=message
    )


def create_search_response(
    results: List[SearchResultData],
    query: str = None,
    total_results: int = None,
    search_time_ms: float = None,
    message: str = None
) -> SearchResponse:
    """Create a search response."""
    response = SearchResponse(
        success=True,
        data=results,
        message=message
    )
    response.query = query
    response.total_results = total_results
    response.search_time_ms = search_time_ms
    return response


# MCP Tool Output Formatters

def format_mcp_sources_output(mcp_output: str) -> SourcesResponse:
    """
    Format MCP get_available_sources tool output into SourcesResponse.
    
    Args:
        mcp_output: Raw string output from get_available_sources MCP tool
        
    Returns:
        SourcesResponse with formatted data
    """
    try:
        import json
        
        # Try to parse JSON output
        if mcp_output.strip().startswith('{') or mcp_output.strip().startswith('['):
            data = json.loads(mcp_output)
        else:
            # Handle plain text output - look for source information
            return SourcesResponse(
                success=False,
                error="Could not parse MCP sources output",
                data=[]
            )
        
        # Convert to SourceData objects
        sources = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    source = SourceData(
                        source_id=item.get("source_id", item.get("id", "unknown")),
                        name=item.get("name", item.get("source_id", "Unknown")),
                        url=item.get("url"),
                        document_count=item.get("document_count", 0),
                        last_updated=item.get("last_updated"),
                        metadata=item.get("metadata", {})
                    )
                    sources.append(source)
        
        return SourcesResponse(
            success=True,
            data=sources,
            message=f"Retrieved {len(sources)} sources"
        )
        
    except Exception as e:
        return SourcesResponse(
            success=False,
            error=f"Failed to format MCP sources output: {str(e)}",
            data=[]
        )


def format_mcp_search_output(mcp_output: str, query: str = None) -> SearchResponse:
    """
    Format MCP perform_rag_query tool output into SearchResponse.
    
    Args:
        mcp_output: Raw string output from perform_rag_query MCP tool
        query: Original search query
        
    Returns:
        SearchResponse with formatted data
    """
    try:
        import json
        
        # Try to parse JSON output
        if mcp_output.strip().startswith('{') or mcp_output.strip().startswith('['):
            data = json.loads(mcp_output)
        else:
            # Handle plain text output - create a single result
            return SearchResponse(
                success=True,
                data=[SearchResultData(
                    id="text_result_1",
                    title="Search Result",
                    content=mcp_output[:500],  # Truncate to max content length
                    relevance_score=1.0
                )],
                message="Converted text output to search result"
            )
        
        # Convert to SearchResultData objects
        results = []
        if isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    result = SearchResultData(
                        id=item.get("id", f"result_{i}"),
                        title=item.get("title", "")[:500],  # Respect max_length
                        content=item.get("content", "")[:5000],  # Respect max_length
                        url=item.get("url"),
                        source_id=item.get("source_id"),
                        relevance_score=float(item.get("relevance_score", 0.0)),
                        metadata=item.get("metadata", {}),
                        snippet_start=item.get("snippet_start"),
                        snippet_end=item.get("snippet_end")
                    )
                    results.append(result)
        
        response = SearchResponse(
            success=True,
            data=results,
            message=f"Found {len(results)} search results"
        )
        response.query = query
        response.total_results = len(results)
        
        return response
        
    except Exception as e:
        return SearchResponse(
            success=False,
            error=f"Failed to format MCP search output: {str(e)}",
            data=[]
        )


def format_mcp_health_output(mcp_connected: bool = True, error: str = None) -> HealthResponse:
    """
    Format health check information into HealthResponse.
    
    Args:
        mcp_connected: Whether MCP server is connected
        error: Any error message
        
    Returns:
        HealthResponse with health status
    """
    try:
        from utils.http_helpers import get_server_stats
        stats = get_server_stats()
        
        health_data = HealthData(
            status="healthy" if mcp_connected and not error else "unhealthy",
            version="1.0.0",
            mcp_connected=mcp_connected,
            uptime_seconds=stats.get("uptime_seconds"),
            memory_usage_mb=stats.get("memory_usage_mb")
        )
        
        return HealthResponse(
            success=mcp_connected and not error,
            data=health_data,
            error=error,
            message="Health check completed"
        )
        
    except Exception as e:
        return HealthResponse(
            success=False,
            error=f"Health check failed: {str(e)}",
            data=HealthData(
                status="unhealthy",
                version="1.0.0",
                mcp_connected=False
            )
        )