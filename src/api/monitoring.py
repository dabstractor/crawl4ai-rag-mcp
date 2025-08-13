"""
Performance monitoring module for Crawl4AI MCP Server API.

This module provides performance monitoring capabilities including:
- Request timing and throughput metrics
- Endpoint-specific performance tracking
- MCP tool execution time tracking
- Memory usage monitoring
"""

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import psutil
import logging
from typing import Callable, Awaitable
from prometheus_client import Counter, Histogram, Gauge, start_http_server

logger = logging.getLogger(__name__)

# Define metrics
REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP request latency", ["method", "endpoint"])
MCP_TOOL_LATENCY = Histogram("mcp_tool_duration_seconds", "MCP tool execution time", ["tool"])
MEMORY_USAGE = Gauge("memory_usage_bytes", "Memory usage in bytes")
CPU_USAGE = Gauge("cpu_usage_percent", "CPU usage percentage")

class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware for monitoring HTTP request performance.
    
    Features:
    - Request timing and throughput metrics
    - Endpoint-specific performance tracking
    - Memory usage monitoring
    """
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable]) -> any:
        """Monitor request performance and record metrics."""
        start_time = time.time()
        
        # Get endpoint for metrics
        endpoint = request.url.path
        method = request.method
        
        # Update memory usage before request
        MEMORY_USAGE.set(psutil.Process().memory_info().rss)
        CPU_USAGE.set(psutil.cpu_percent())
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Record metrics
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=response.status_code).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
            
            # Update memory usage after request
            MEMORY_USAGE.set(psutil.Process().memory_info().rss)
            CPU_USAGE.set(psutil.cpu_percent())
            
            # Add timing header
            response.headers["X-Process-Time"] = str(duration)
            
            return response
        except Exception as e:
            duration = time.time() - start_time
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=500).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
            
            # Update memory usage after failed request
            MEMORY_USAGE.set(psutil.Process().memory_info().rss)
            CPU_USAGE.set(psutil.cpu_percent())
            
            raise

async def time_mcp_tool(tool_name: str, coroutine) -> any:
    """
    Time an MCP tool execution and record metrics.
    
    Args:
        tool_name: Name of the MCP tool being executed
        coroutine: The coroutine to execute
        
    Returns:
        The result of the coroutine execution
    """
    start_time = time.time()
    try:
        result = await coroutine
        duration = time.time() - start_time
        MCP_TOOL_LATENCY.labels(tool=tool_name).observe(duration)
        return result
    except Exception as e:
        duration = time.time() - start_time
        MCP_TOOL_LATENCY.labels(tool=tool_name).observe(duration)
        raise

def add_performance_monitoring(app: FastAPI, metrics_port: int = 8000) -> None:
    """
    Add performance monitoring to the FastAPI app.
    
    Args:
        app: FastAPI application instance
        metrics_port: Port to serve metrics on (default: 8000)
    """
    try:
        # Start Prometheus metrics server
        start_http_server(metrics_port)
        logger.info(f"Prometheus metrics server started on port {metrics_port}")
    except Exception as e:
        logger.warning(f"Failed to start Prometheus metrics server on port {metrics_port}: {e}")
    
    # Add middleware
    app.add_middleware(PerformanceMonitoringMiddleware)
    logger.info("Performance monitoring middleware added")