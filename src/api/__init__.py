"""
HTTP API layer for Crawl4AI MCP Server.

This module provides HTTP REST API endpoints that wrap the existing MCP tools
to enable browser-based UI access while maintaining compatibility with 
MCP protocol clients.
"""

__version__ = "1.0.0"
__author__ = "Crawl4AI MCP HTTP API"

from .endpoints import *
from .middleware import *
from .responses import *
from .monitoring import *

__all__ = [
    'endpoints',
    'middleware', 
    'responses',
    'monitoring'
]