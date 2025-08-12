"""
HTTP utility functions for Crawl4AI MCP Server API.

This module provides utility functions to support HTTP API implementation,
including MCP tool integration and response formatting.
"""

import asyncio
import json
import time
import logging
import psutil
import os
from typing import Any, Dict, List, Optional, Callable, Awaitable
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Server startup time for uptime calculation
SERVER_START_TIME = time.time()


async def call_mcp_tool(tool_name: str, context, **kwargs) -> Dict[str, Any]:
    """
    Call an MCP tool and return the result in a standardized format.
    
    Args:
        tool_name: Name of the MCP tool to call
        context: MCP context object
        **kwargs: Arguments to pass to the MCP tool
        
    Returns:
        Dict containing success status, data, and any errors
    """
    try:
        logger.info(f"Calling MCP tool '{tool_name}' with args: {kwargs}")
        
        # This will be implemented to actually call the MCP tools
        # For now, return a placeholder structure
        
        result = {
            "success": True,
            "data": f"MCP tool '{tool_name}' called successfully",
            "error": None,
            "execution_time_ms": 0.0
        }
        
        logger.info(f"MCP tool '{tool_name}' completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"MCP tool '{tool_name}' failed: {e}")
        return {
            "success": False,
            "data": None,
            "error": str(e),
            "execution_time_ms": 0.0
        }


def get_server_stats() -> Dict[str, Any]:
    """
    Get server statistics including uptime and memory usage.
    
    Returns:
        Dict containing server statistics
    """
    try:
        # Calculate uptime
        uptime_seconds = time.time() - SERVER_START_TIME
        
        # Get memory usage
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_usage_mb = memory_info.rss / 1024 / 1024
        
        # Get CPU usage
        cpu_percent = process.cpu_percent()
        
        return {
            "uptime_seconds": uptime_seconds,
            "memory_usage_mb": round(memory_usage_mb, 2),
            "cpu_percent": cpu_percent,
            "pid": os.getpid(),
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
        }
    except Exception as e:
        logger.error(f"Failed to get server stats: {e}")
        return {
            "uptime_seconds": time.time() - SERVER_START_TIME,
            "memory_usage_mb": 0.0,
            "cpu_percent": 0.0,
            "error": str(e)
        }


def format_search_results(raw_results: List[Dict], query: str = None) -> Dict[str, Any]:
    """
    Format raw search results into standardized API format.
    
    Args:
        raw_results: Raw search results from MCP tools
        query: Original search query
        
    Returns:
        Formatted search results
    """
    try:
        formatted_results = []
        
        for i, result in enumerate(raw_results):
            formatted_result = {
                "id": result.get("id", f"result_{i}"),
                "title": result.get("title", ""),
                "content": result.get("content", ""),
                "url": result.get("url"),
                "source_id": result.get("source_id"),
                "relevance_score": result.get("relevance_score", 0.0),
                "metadata": result.get("metadata", {}),
                "snippet_start": result.get("snippet_start"),
                "snippet_end": result.get("snippet_end")
            }
            formatted_results.append(formatted_result)
        
        return {
            "results": formatted_results,
            "query": query,
            "total_results": len(formatted_results),
            "formatted_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to format search results: {e}")
        return {
            "results": [],
            "query": query,
            "total_results": 0,
            "error": str(e)
        }


def format_sources_list(raw_sources: List[Dict]) -> List[Dict[str, Any]]:
    """
    Format raw sources data into standardized API format.
    
    Args:
        raw_sources: Raw sources data from MCP tools
        
    Returns:
        Formatted sources list
    """
    try:
        formatted_sources = []
        
        for source in raw_sources:
            formatted_source = {
                "source_id": source.get("source_id", source.get("id", "")),
                "name": source.get("name", source.get("source_id", "Unknown")),
                "url": source.get("url"),
                "document_count": source.get("document_count", 0),
                "last_updated": source.get("last_updated"),
                "metadata": source.get("metadata", {})
            }
            formatted_sources.append(formatted_source)
        
        return formatted_sources
        
    except Exception as e:
        logger.error(f"Failed to format sources list: {e}")
        return []


async def with_timeout(coro: Awaitable, timeout_seconds: float = 30.0) -> Dict[str, Any]:
    """
    Execute a coroutine with a timeout.
    
    Args:
        coro: Coroutine to execute
        timeout_seconds: Timeout in seconds
        
    Returns:
        Result dict with success status and data/error
    """
    try:
        result = await asyncio.wait_for(coro, timeout=timeout_seconds)
        return {
            "success": True,
            "data": result,
            "error": None
        }
    except asyncio.TimeoutError:
        logger.error(f"Operation timed out after {timeout_seconds} seconds")
        return {
            "success": False,
            "data": None,
            "error": f"Operation timed out after {timeout_seconds} seconds"
        }
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        return {
            "success": False,
            "data": None,
            "error": str(e)
        }


def validate_query_params(
    query: str,
    match_count: int = 5,
    source: str = None
) -> Dict[str, Any]:
    """
    Validate and sanitize query parameters.
    
    Args:
        query: Search query string
        match_count: Number of results to return
        source: Optional source filter
        
    Returns:
        Validation result with sanitized parameters
    """
    errors = []
    
    # Validate query
    if not query or not query.strip():
        errors.append("Query parameter is required and cannot be empty")
    elif len(query.strip()) > 1000:
        errors.append("Query parameter is too long (max 1000 characters)")
    
    # Validate match_count
    if match_count < 1 or match_count > 50:
        errors.append("Match count must be between 1 and 50")
    
    # Validate source
    if source and len(source) > 100:
        errors.append("Source parameter is too long (max 100 characters)")
    
    if errors:
        return {
            "valid": False,
            "errors": errors,
            "params": None
        }
    
    return {
        "valid": True,
        "errors": [],
        "params": {
            "query": query.strip(),
            "match_count": match_count,
            "source": source.strip() if source else None
        }
    }


def validate_search_params(query: str, source: str = None, match_count: int = 10) -> Dict[str, Any]:
    """
    Validate and prepare search parameters for MCP tool.
    
    Args:
        query: Search query string
        source: Optional source filter
        match_count: Number of results to return
        
    Returns:
        Dict containing validated parameters or error information
        
    Raises:
        ValueError: If parameters are invalid
    """
    if not query or not query.strip():
        raise ValueError("Query parameter cannot be empty")
        
    if match_count < 1 or match_count > 100:
        raise ValueError("match_count must be between 1 and 100")
        
    return {
        "query": query.strip(),
        "source": source.strip() if source else None,
        "match_count": match_count
    }


def format_mcp_response(response: Any) -> Dict[str, Any]:
    """
    Format MCP tool response for HTTP API.
    
    Args:
        response: Raw response from MCP tool
        
    Returns:
        Dict containing formatted response data
    """
    try:
        # Handle string responses
        if isinstance(response, str):
            return parse_mcp_response(response)
        
        # Handle dict responses
        elif isinstance(response, dict):
            return response
            
        # Handle list responses
        elif isinstance(response, list):
            return {"type": "list", "data": response}
            
        # Handle other types
        else:
            return {"type": "unknown", "data": str(response)}
            
    except Exception as e:
        logger.error(f"Failed to format MCP response: {e}")
        return {
            "type": "error",
            "data": None,
            "error": str(e)
        }


def extract_request_metadata(request) -> Dict[str, Any]:
    """
    Extract metadata from HTTP request for logging and monitoring.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Dict containing request metadata
    """
    try:
        # Extract client information
        client_info = {}
        if hasattr(request, 'client') and request.client:
            client_info = {
                "host": getattr(request.client, "host", "unknown"),
                "port": getattr(request.client, "port", "unknown")
            }
        
        # Extract headers (safely)
        headers = {}
        if hasattr(request, 'headers'):
            # Only extract safe headers for logging
            safe_headers = ['user-agent', 'content-type', 'accept']
            for header in safe_headers:
                if header in request.headers:
                    headers[header] = request.headers[header]
        
        return {
            "method": getattr(request, "method", "unknown"),
            "url": str(getattr(request, "url", "unknown")),
            "client": client_info,
            "headers": headers,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to extract request metadata: {e}")
        return {"error": str(e)}


# TypeVar for generic async function
T = type(None)

async def async_with_timeout(coro: Awaitable[T], timeout_seconds: float = 10.0) -> T:
    """
    Run a coroutine with a timeout.
    
    Args:
        coro: Coroutine to execute
        timeout_seconds: Timeout in seconds
        
    Returns:
        Result of the coroutine
        
    Raises:
        asyncio.TimeoutError: If the operation times out
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise asyncio.TimeoutError(f"Operation timed out after {timeout_seconds} seconds")
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise


def parse_mcp_response(mcp_result: str) -> Dict[str, Any]:
    """
    Parse MCP tool response string into structured data.
    
    Args:
        mcp_result: Raw string result from MCP tool
        
    Returns:
        Parsed structured data
    """
    try:
        # Try to parse as JSON first
        if mcp_result.strip().startswith('{') or mcp_result.strip().startswith('['):
            return json.loads(mcp_result)
        
        # If not JSON, return as plain text
        return {
            "type": "text",
            "content": mcp_result,
            "parsed_at": datetime.now().isoformat()
        }
        
    except json.JSONDecodeError:
        # Fall back to plain text
        return {
            "type": "text",
            "content": mcp_result,
            "parsed_at": datetime.now().isoformat(),
            "parse_error": "Failed to parse as JSON"
        }
    except Exception as e:
        logger.error(f"Failed to parse MCP response: {e}")
        return {
            "type": "error",
            "content": mcp_result,
            "error": str(e),
            "parsed_at": datetime.now().isoformat()
        }


class APIMetrics:
    """Simple metrics collector for API endpoints."""
    
    def __init__(self):
        self.request_counts = {}
        self.response_times = {}
        self.error_counts = {}
    
    def record_request(self, endpoint: str, response_time: float, success: bool):
        """Record a request metric."""
        # Request count
        self.request_counts[endpoint] = self.request_counts.get(endpoint, 0) + 1
        
        # Response time
        if endpoint not in self.response_times:
            self.response_times[endpoint] = []
        self.response_times[endpoint].append(response_time)
        
        # Error count
        if not success:
            self.error_counts[endpoint] = self.error_counts.get(endpoint, 0) + 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics summary."""
        metrics = {
            "total_requests": sum(self.request_counts.values()),
            "total_errors": sum(self.error_counts.values()),
            "endpoints": {}
        }
        
        for endpoint in self.request_counts:
            times = self.response_times.get(endpoint, [])
            avg_time = sum(times) / len(times) if times else 0
            
            metrics["endpoints"][endpoint] = {
                "request_count": self.request_counts[endpoint],
                "error_count": self.error_counts.get(endpoint, 0),
                "avg_response_time_ms": round(avg_time * 1000, 2),
                "success_rate": (
                    (self.request_counts[endpoint] - self.error_counts.get(endpoint, 0)) 
                    / self.request_counts[endpoint]
                ) if self.request_counts[endpoint] > 0 else 0
            }
        
        return metrics


# Global metrics instance
api_metrics = APIMetrics()