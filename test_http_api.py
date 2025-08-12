#!/usr/bin/env python3
"""
Test script for Crawl4AI MCP HTTP API endpoints.

This script tests all the implemented HTTP API endpoints to verify they are working correctly.
"""

import requests
import json
import sys
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8051"
API_PREFIX = "/api"
TIMEOUT = 30

def test_endpoint(url: str, method: str = "GET", params: Dict = None) -> Dict[str, Any]:
    """
    Test an HTTP endpoint and return the result.
    
    Args:
        url: The full URL to test
        method: HTTP method (default: GET)
        params: Query parameters for GET requests
        
    Returns:
        Dictionary with test results
    """
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params, timeout=TIMEOUT)
        else:
            response = requests.request(method, url, timeout=TIMEOUT)
            
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "error": None
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "status_code": None,
            "response": None,
            "error": str(e)
        }
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "status_code": response.status_code if 'response' in locals() else None,
            "response": response.text if 'response' in locals() else None,
            "error": f"JSON decode error: {str(e)}"
        }

def test_health_endpoint() -> Dict[str, Any]:
    """Test the health check endpoint."""
    print("Testing /api/health endpoint...")
    result = test_endpoint(f"{BASE_URL}{API_PREFIX}/health")
    
    if result["success"]:
        data = result["response"]
        if isinstance(data, dict) and data.get("success"):
            print("  ✅ Health endpoint working correctly")
            print(f"  📊 Status: {data.get('data', {}).get('status', 'unknown')}")
            print(f"  🔌 MCP Connected: {data.get('data', {}).get('mcp_connected', False)}")
        else:
            print("  ⚠️  Health endpoint returned unexpected response")
            print(f"  Response: {data}")
    else:
        print("  ❌ Health endpoint failed")
        if result["error"]:
            print(f"  Error: {result['error']}")
        else:
            print(f"  Status Code: {result['status_code']}")
            
    return result

def test_sources_endpoint() -> Dict[str, Any]:
    """Test the sources endpoint."""
    print("Testing /api/sources endpoint...")
    result = test_endpoint(f"{BASE_URL}{API_PREFIX}/sources")
    
    if result["success"]:
        data = result["response"]
        if isinstance(data, dict) and data.get("success"):
            sources_count = len(data.get("data", []))
            print("  ✅ Sources endpoint working correctly")
            print(f"  📊 Found {sources_count} sources")
        else:
            print("  ⚠️  Sources endpoint returned unexpected response")
            print(f"  Response: {data}")
    else:
        print("  ❌ Sources endpoint failed")
        if result["error"]:
            print(f"  Error: {result['error']}")
        else:
            print(f"  Status Code: {result['status_code']}")
            
    return result

def test_search_endpoint() -> Dict[str, Any]:
    """Test the search endpoint."""
    print("Testing /api/search endpoint...")
    result = test_endpoint(
        f"{BASE_URL}{API_PREFIX}/search",
        params={"query": "test search", "match_count": 1}
    )
    
    if result["success"]:
        data = result["response"]
        if isinstance(data, dict) and data.get("success"):
            results_count = data.get("total_results", 0)
            print("  ✅ Search endpoint working correctly")
            print(f"  📊 Found {results_count} results")
        else:
            print("  ⚠️  Search endpoint returned unexpected response")
            print(f"  Response: {data}")
    else:
        print("  ❌ Search endpoint failed")
        if result["error"]:
            print(f"  Error: {result['error']}")
        else:
            print(f"  Status Code: {result['status_code']}")
            
    return result

def test_code_examples_endpoint() -> Dict[str, Any]:
    """Test the code examples endpoint."""
    print("Testing /api/code-examples endpoint...")
    result = test_endpoint(
        f"{BASE_URL}{API_PREFIX}/code-examples",
        params={"query": "python example", "match_count": 1}
    )
    
    if result["success"]:
        data = result["response"]
        if isinstance(data, dict) and data.get("success"):
            results_count = data.get("total_results", 0)
            print("  ✅ Code examples endpoint working correctly")
            print(f"  📊 Found {results_count} results")
        else:
            print("  ⚠️  Code examples endpoint returned unexpected response")
            print(f"  Response: {data}")
    else:
        print("  ❌ Code examples endpoint failed")
        if result["error"]:
            print(f"  Error: {result['error']}")
        else:
            print(f"  Status Code: {result['status_code']}")
            
    return result

def test_root_endpoint() -> Dict[str, Any]:
    """Test the root endpoint."""
    print("Testing root endpoint (/)...")
    result = test_endpoint(f"{BASE_URL}/")
    
    if result["success"]:
        print("  ✅ Root endpoint accessible")
        print(f"  Response type: {type(result['response'])}")
    else:
        print("  ⚠️  Root endpoint returned non-200 status")
        if result["error"]:
            print(f"  Error: {result['error']}")
        else:
            print(f"  Status Code: {result['status_code']}")
            
    return result

def test_docs_endpoint() -> Dict[str, Any]:
    """Test the docs endpoint."""
    print("Testing docs endpoint (/docs)...")
    result = test_endpoint(f"{BASE_URL}/docs")
    
    if result["success"]:
        print("  ✅ Docs endpoint accessible")
    else:
        print("  ⚠️  Docs endpoint not accessible")
        if result["error"]:
            print(f"  Error: {result['error']}")
        else:
            print(f"  Status Code: {result['status_code']}")
            
    return result

def main():
    """Main test function."""
    print(f"🧪 Testing Crawl4AI MCP HTTP API Endpoints")
    print(f"📍 Base URL: {BASE_URL}")
    print(f"🚦 API Prefix: {API_PREFIX}")
    print("-" * 50)
    
    # Test endpoints
    tests = [
        test_root_endpoint,
        test_docs_endpoint,
        test_health_endpoint,
        test_sources_endpoint,
        test_search_endpoint,
        test_code_examples_endpoint
    ]
    
    results = []
    passed = 0
    failed = 0
    
    for test_func in tests:
        print()
        result = test_func()
        results.append(result)
        if result["success"]:
            passed += 1
        else:
            failed += 1
    
    print()
    print("-" * 50)
    print(f"📊 Test Results Summary:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Total: {len(tests)}")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())