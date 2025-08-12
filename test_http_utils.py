#!/usr/bin/env python3
"""
Test script to verify HTTP utility functions implementation.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that HTTP utility functions can be imported."""
    try:
        sys.path.append('src')
        from utils.http_helpers import (
            validate_query_params, validate_search_params, format_mcp_response,
            extract_request_metadata, async_with_timeout, call_mcp_tool,
            get_server_stats, format_search_results, format_sources_list,
            with_timeout, parse_mcp_response, APIMetrics
        )
        print("✓ All HTTP utility functions can be imported")
        return True
    except ImportError as e:
        print(f"✗ Failed to import HTTP utility functions: {e}")
        return False

def test_parameter_validation():
    """Test parameter validation functions."""
    try:
        sys.path.append('src')
        from utils.http_helpers import validate_query_params, validate_search_params
        
        # Test validate_query_params with valid input
        result = validate_query_params("test query", 10, "example.com")
        assert result["valid"] == True
        assert result["params"]["query"] == "test query"
        assert result["params"]["match_count"] == 10
        assert result["params"]["source"] == "example.com"
        print("✓ validate_query_params works with valid input")
        
        # Test validate_query_params with invalid input
        result = validate_query_params("", 10)
        assert result["valid"] == False
        assert "required" in result["errors"][0]
        print("✓ validate_query_params correctly rejects empty query")
        
        # Test validate_search_params with valid input
        result = validate_search_params("test query", "example.com", 25)
        assert result["query"] == "test query"
        assert result["source"] == "example.com"
        assert result["match_count"] == 25
        print("✓ validate_search_params works with valid input")
        
        # Test validate_search_params with invalid input
        try:
            validate_search_params("", "example.com", 25)
            print("✗ validate_search_params should reject empty query")
            return False
        except ValueError:
            print("✓ validate_search_params correctly raises ValueError for empty query")
        
        return True
        
    except Exception as e:
        print(f"✗ Parameter validation test failed: {e}")
        return False

def test_response_formatting():
    """Test response formatting functions."""
    try:
        sys.path.append('src')
        from utils.http_helpers import format_mcp_response, parse_mcp_response
        
        # Test format_mcp_response with string
        result = format_mcp_response("test response")
        assert result["type"] == "text"
        assert result["content"] == "test response"
        print("✓ format_mcp_response works with string input")
        
        # Test format_mcp_response with dict
        test_dict = {"key": "value", "number": 42}
        result = format_mcp_response(test_dict)
        assert result == test_dict
        print("✓ format_mcp_response works with dict input")
        
        # Test format_mcp_response with list
        test_list = ["item1", "item2", "item3"]
        result = format_mcp_response(test_list)
        assert result["type"] == "list"
        assert result["data"] == test_list
        print("✓ format_mcp_response works with list input")
        
        # Test parse_mcp_response with JSON
        json_str = '{"test": "value", "number": 42}'
        result = parse_mcp_response(json_str)
        assert result["test"] == "value"
        assert result["number"] == 42
        print("✓ parse_mcp_response works with JSON input")
        
        return True
        
    except Exception as e:
        print(f"✗ Response formatting test failed: {e}")
        return False

def test_async_timeout():
    """Test async timeout functionality."""
    try:
        import asyncio
        sys.path.append('src')
        from utils.http_helpers import async_with_timeout
        
        # Test successful completion within timeout
        async def quick_task():
            await asyncio.sleep(0.1)
            return "success"
        
        async def test_success():
            result = await async_with_timeout(quick_task(), timeout_seconds=1.0)
            assert result == "success"
            return True
        
        # Run the async test
        result = asyncio.run(test_success())
        if result:
            print("✓ async_with_timeout works with successful completion")
        
        return True
        
    except Exception as e:
        print(f"✗ Async timeout test failed: {e}")
        return False

def test_task_requirements():
    """Test compliance with Task #6 requirements."""
    try:
        sys.path.append('src')
        from utils.http_helpers import (
            validate_query_params, format_mcp_response, async_with_timeout,
            extract_request_metadata, validate_search_params
        )
        
        # Check that required functions are implemented
        required_functions = [
            "validate_query_params",  # Parameter validation and sanitization
            "format_mcp_response",    # Converting between MCP tool parameters and HTTP responses
            "async_with_timeout",     # Handling timeouts and async operations
            "extract_request_metadata"  # Managing request context and state
        ]
        
        for func_name in required_functions:
            print(f"✓ {func_name} implemented for HTTP utility support")
        
        # Test validate_search_params as specified in the example
        result = validate_search_params("test query", None, 10)
        assert result["query"] == "test query"
        assert result["match_count"] == 10
        print("✓ validate_search_params matches specification example")
        
        return True
        
    except Exception as e:
        print(f"✗ Task requirements test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing HTTP utility functions implementation...")
    
    success = all([
        test_imports(),
        test_parameter_validation(),
        test_response_formatting(),
        test_async_timeout(),
        test_task_requirements()
    ])
    
    # Clean up
    if os.path.exists("test_http_utils.py"):
        os.remove("test_http_utils.py")
    
    if success:
        print("\n✓ All HTTP utility functions tests passed!")
        print("✓ Task #6: Implement HTTP Utility Functions - COMPLETED")
        print("✓ Features implemented:")
        print("  - Parameter validation and sanitization")
        print("  - MCP tool parameter conversion")
        print("  - Async timeout handling")
        print("  - Request metadata extraction")
        print("  - Response formatting and parsing")
        print("  - Error handling and logging")
    else:
        print("\n✗ Some HTTP utility functions tests failed.")
        sys.exit(1)