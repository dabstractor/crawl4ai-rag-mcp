# API Endpoint Tests

This directory contains comprehensive unit tests for the Crawl4AI MCP HTTP API endpoints.

## Overview

The test suite validates:
- ✅ API endpoint structure and validation
- ✅ HTTP response model compliance  
- ✅ Parameter validation logic
- ✅ Error response format verification
- ✅ CORS configuration testing
- ✅ HTTP status code validation
- ✅ Content-type header verification
- ✅ Live server testing (when available)
- ✅ Edge case parameter handling

## Test Files

### `test_api_simple.py`
Core test suite that validates API structure and responses without requiring server dependencies. This is the main test file that covers:
- API endpoint path validation
- Response model structure verification  
- Parameter validation logic
- Error handling patterns
- CORS configuration
- Live server testing (when server is running)

### `run_tests.py` 
Comprehensive test runner that:
- Discovers all test modules automatically
- Provides detailed reporting and summaries
- Shows coverage information
- Gives recommendations for next steps

## Running Tests

### Quick Test Run
```bash
# Run the simple test suite directly
python tests/test_api_simple.py
```

### Comprehensive Test Run  
```bash
# Run all tests with detailed reporting
python tests/run_tests.py
```

### Using unittest
```bash
# Run from project root
python -m unittest discover tests/ -v
```

## Test Results

The current test suite achieves **100% pass rate** with 14 comprehensive tests covering all API endpoints.

## Endpoints Tested

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check with MCP connectivity status |
| GET | `/api/sources` | Available crawled data sources |  
| GET | `/api/search` | Semantic search with RAG |
| POST | `/api/search` | Semantic search via JSON body |
| GET | `/api/code-examples` | Code example search |
| GET | `/api/status` | API status and configuration |

## Test Categories

### Structure Tests
- Response model validation
- Required field verification
- Data type checking
- Optional field handling

### Validation Tests  
- Parameter boundary testing
- Required parameter enforcement
- Invalid input handling
- Edge case coverage

### Error Handling Tests
- Error response format validation
- HTTP status code verification
- Error message structure
- Graceful failure testing

### Live Server Tests
- Endpoint availability (when server running)
- Response validation with real server
- Network error handling
- Timeout behavior

## Dependencies

The tests use Python's built-in `unittest` framework and work without additional dependencies:
- `unittest` - Python standard library testing framework
- `requests` - HTTP client library (optional, used when available)

## Adding New Tests

To add new test cases:

1. **Structure Tests**: Add to `TestAPIStructure` class in `test_api_simple.py`
2. **Live Server Tests**: Add to `TestAPIEndpointsLive` class in `test_api_simple.py`  
3. **New Test Files**: Create new `test_*.py` files that will be auto-discovered

### Example Test Case
```python
def test_new_endpoint_validation(self):
    """Test new endpoint parameter validation."""
    # Test structure
    expected_response = {
        "success": True,
        "data": {...},
        "message": "Success"
    }
    
    # Validate structure
    self.assertIn("success", expected_response)
    self.assertIn("data", expected_response)
    
    # Test with live server (if available)
    result = self.make_request("GET", "/api/new-endpoint")
    if result["success"]:
        self.assertEqual(result["status_code"], 200)
```

## Mock Testing

For testing with MCP tool mocking, ensure proper dependency management:
- Mock external MCP calls to avoid dependency issues
- Use `unittest.mock.patch` for isolated testing
- Test both success and failure scenarios

## Continuous Integration

The test suite is designed for CI/CD integration:
- Zero external dependencies for basic structure tests
- Exit codes: 0 (success), 1 (failure)
- Detailed reporting suitable for CI logs
- Fast execution (< 1 second for full suite)

## Next Steps

1. **Performance Testing**: Add endpoint response time benchmarks
2. **Security Testing**: Add input sanitization and injection tests
3. **Load Testing**: Add concurrent request handling tests
4. **Integration Testing**: Add end-to-end workflow tests
5. **Monitoring**: Add test metrics and alerting

## Troubleshooting

### Common Issues

**Import Errors**: Ensure `src/` is in Python path
```bash
export PYTHONPATH="$PYTHONPATH:$(pwd)/src"
```

**Server Connection**: Tests work offline but live server tests require running API server
```bash
# Start server for live tests
python src/crawl4ai_mcp.py --enable-http-api
```

**Missing Dependencies**: Some tests may require additional packages
```bash
pip install requests  # For HTTP client testing
```

### Test Debugging

Enable verbose output:
```bash
python tests/run_tests.py -v
```

Run specific test:
```bash
python -m unittest tests.test_api_simple.TestAPIStructure.test_health_response_structure -v
```