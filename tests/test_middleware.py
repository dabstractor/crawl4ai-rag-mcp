#!/usr/bin/env python3
"""
Unit tests for middleware functionality.

This test suite validates the RequestLoggingMiddleware implementation
including correlation IDs, query parameter logging, configurable log levels,
and error handling.
"""

import unittest
import sys
import os
import logging
import time
import uuid
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from fastapi import Request, Response, FastAPI
    from starlette.types import ASGIApp
    from src.api.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware, get_client_ip
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


class TestRequestLoggingMiddleware(unittest.TestCase):
    """Test RequestLoggingMiddleware functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not FASTAPI_AVAILABLE:
            self.skipTest("FastAPI not available")
            
        # Create mock app
        self.mock_app = Mock(spec=ASGIApp)
        self.middleware = RequestLoggingMiddleware(self.mock_app)
        
        # Set up logging capture
        self.log_stream = StringIO()
        self.log_handler = logging.StreamHandler(self.log_stream)
        self.logger = logging.getLogger('src.api.middleware')
        self.logger.addHandler(self.log_handler)
        self.logger.setLevel(logging.INFO)
        
    def tearDown(self):
        """Clean up test fixtures."""
        if hasattr(self, 'logger'):
            self.logger.removeHandler(self.log_handler)
            
    def create_mock_request(self, method="GET", path="/test", query_params=None, headers=None):
        """Create a mock request object."""
        request = Mock(spec=Request)
        request.method = method
        request.url.path = path
        
        # Set up query parameters
        if query_params:
            request.query_params = query_params
            request.url.__str__ = Mock(return_value=f"{path}?{'&'.join([f'{k}={v}' for k, v in query_params.items()])}")
        else:
            request.query_params = {}
            request.url.__str__ = Mock(return_value=path)
            
        # Set up headers
        if headers is None:
            headers = {}
        request.headers = headers
        request.headers.get = lambda key, default=None: headers.get(key, default)
        
        # Set up client
        client_mock = Mock()
        client_mock.host = "127.0.0.1"
        request.client = client_mock
        
        return request
        
    def create_mock_response(self, status_code=200, headers=None):
        """Create a mock response object."""
        response = Mock(spec=Response)
        response.status_code = status_code
        if headers is None:
            headers = {}
        response.headers = headers
        return response

    @patch.dict(os.environ, {"REQUEST_LOG_LEVEL": "DEBUG"})
    def test_configurable_log_level(self):
        """Test that log level is configurable via environment variable."""
        middleware = RequestLoggingMiddleware(self.mock_app)
        self.assertEqual(middleware.log_level, logging.DEBUG)
        
    @patch.dict(os.environ, {"REQUEST_LOG_LEVEL": "ERROR"})
    def test_configurable_log_level_error(self):
        """Test ERROR log level configuration."""
        middleware = RequestLoggingMiddleware(self.mock_app)
        self.assertEqual(middleware.log_level, logging.ERROR)
        
    def test_default_log_level(self):
        """Test default log level when env var not set."""
        # Remove env var if it exists
        if "REQUEST_LOG_LEVEL" in os.environ:
            del os.environ["REQUEST_LOG_LEVEL"]
        middleware = RequestLoggingMiddleware(self.mock_app)
        self.assertEqual(middleware.log_level, logging.INFO)

    async def test_request_logging_with_correlation_id(self):
        """Test that requests are logged with correlation IDs."""
        request = self.create_mock_request("GET", "/api/test")
        response = self.create_mock_response(200)
        
        # Mock the call_next function
        call_next = Mock(return_value=response)
        
        # Process request
        result = await self.middleware.dispatch(request, call_next)
        
        # Verify response headers contain correlation ID
        self.assertIn("X-Request-ID", result.headers)
        self.assertIn("X-Process-Time", result.headers)
        
        # Verify UUID format of request ID
        request_id = result.headers["X-Request-ID"]
        try:
            uuid.UUID(request_id)
        except ValueError:
            self.fail("X-Request-ID is not a valid UUID")
            
    async def test_query_parameter_logging(self):
        """Test that query parameters are properly logged."""
        query_params = {"search": "test", "limit": "10"}
        request = self.create_mock_request("GET", "/api/search", query_params=query_params)
        response = self.create_mock_response(200)
        
        call_next = Mock(return_value=response)
        
        # Process request
        await self.middleware.dispatch(request, call_next)
        
        # Check logs contain query parameters
        log_output = self.log_stream.getvalue()
        self.assertIn("search=test", log_output)
        self.assertIn("limit=10", log_output)
        
    async def test_error_handling_and_logging(self):
        """Test that errors are properly logged with context."""
        request = self.create_mock_request("POST", "/api/error")
        
        # Mock call_next to raise an exception
        test_exception = Exception("Test error")
        call_next = Mock(side_effect=test_exception)
        
        # Process request and expect exception to be re-raised
        with self.assertRaises(Exception):
            await self.middleware.dispatch(request, call_next)
            
        # Check error was logged
        log_output = self.log_stream.getvalue()
        self.assertIn("Error", log_output)
        self.assertIn("Test error", log_output)
        self.assertIn("POST", log_output)
        self.assertIn("/api/error", log_output)
        
    async def test_timing_measurement(self):
        """Test that timing is accurately measured."""
        request = self.create_mock_request("GET", "/api/slow")
        response = self.create_mock_response(200)
        
        # Mock call_next with a delay
        async def slow_call_next(req):
            await asyncio.sleep(0.1)  # 100ms delay
            return response
            
        call_next = slow_call_next
        
        start_time = time.time()
        result = await self.middleware.dispatch(request, call_next)
        end_time = time.time()
        
        # Verify timing header exists and is reasonable
        process_time = float(result.headers["X-Process-Time"])
        actual_time = end_time - start_time
        
        # Allow for some variance but should be close to actual time
        self.assertGreater(process_time, 0.05)  # At least 50ms
        self.assertLess(process_time, actual_time + 0.05)  # Within 50ms of actual


class TestGetClientIPUtility(unittest.TestCase):
    """Test the get_client_ip utility function."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not FASTAPI_AVAILABLE:
            self.skipTest("FastAPI not available")
            
    def create_mock_request_with_headers(self, headers):
        """Create a mock request with specific headers."""
        request = Mock(spec=Request)
        request.headers = headers
        request.headers.get = lambda key, default=None: headers.get(key, default)
        
        # Mock client
        client_mock = Mock()
        client_mock.host = "127.0.0.1"
        request.client = client_mock
        
        return request
        
    def test_x_forwarded_for_header(self):
        """Test X-Forwarded-For header parsing."""
        headers = {"X-Forwarded-For": "192.168.1.100, 10.0.0.1"}
        request = self.create_mock_request_with_headers(headers)
        
        client_ip = get_client_ip(request)
        self.assertEqual(client_ip, "192.168.1.100")
        
    def test_x_real_ip_header(self):
        """Test X-Real-IP header parsing."""
        headers = {"X-Real-IP": "203.0.113.195"}
        request = self.create_mock_request_with_headers(headers)
        
        client_ip = get_client_ip(request)
        self.assertEqual(client_ip, "203.0.113.195")
        
    def test_forwarded_for_priority(self):
        """Test that X-Forwarded-For takes priority over X-Real-IP."""
        headers = {
            "X-Forwarded-For": "192.168.1.100",
            "X-Real-IP": "203.0.113.195"
        }
        request = self.create_mock_request_with_headers(headers)
        
        client_ip = get_client_ip(request)
        self.assertEqual(client_ip, "192.168.1.100")
        
    def test_fallback_to_client_host(self):
        """Test fallback to client.host when no forwarded headers."""
        headers = {}
        request = self.create_mock_request_with_headers(headers)
        
        client_ip = get_client_ip(request)
        self.assertEqual(client_ip, "127.0.0.1")
        
    def test_no_client_fallback(self):
        """Test fallback when no client object."""
        request = Mock(spec=Request)
        request.headers = {}
        request.headers.get = lambda key, default=None: default
        request.client = None
        
        client_ip = get_client_ip(request)
        self.assertEqual(client_ip, "unknown")


class TestSecurityHeadersMiddleware(unittest.TestCase):
    """Test SecurityHeadersMiddleware functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not FASTAPI_AVAILABLE:
            self.skipTest("FastAPI not available")
            
        # Create mock app
        self.mock_app = Mock(spec=ASGIApp)
        self.middleware = SecurityHeadersMiddleware(self.mock_app)
        
    def create_mock_request(self, method="GET", path="/test"):
        """Create a mock request object."""
        request = Mock(spec=Request)
        request.method = method
        request.url.path = path
        return request
        
    def create_mock_response(self, status_code=200, headers=None):
        """Create a mock response object."""
        response = Mock(spec=Response)
        response.status_code = status_code
        if headers is None:
            headers = {}
        response.headers = headers
        return response

    async def test_basic_security_headers(self):
        """Test that basic security headers are added."""
        request = self.create_mock_request("GET", "/api/test")
        response = self.create_mock_response(200)
        
        # Mock the call_next function
        call_next = Mock(return_value=response)
        
        # Process request
        result = await self.middleware.dispatch(request, call_next)
        
        # Verify security headers are present
        self.assertEqual(result.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(result.headers["X-Frame-Options"], "DENY")
        self.assertEqual(result.headers["X-XSS-Protection"], "1; mode=block")
        self.assertIn("Content-Security-Policy", result.headers)
        
    async def test_default_csp_header(self):
        """Test that default CSP header is set when no env var."""
        request = self.create_mock_request("GET", "/api/test")
        response = self.create_mock_response(200)
        
        # Ensure no CSP env var is set
        if "CONTENT_SECURITY_POLICY" in os.environ:
            del os.environ["CONTENT_SECURITY_POLICY"]
            
        call_next = Mock(return_value=response)
        result = await self.middleware.dispatch(request, call_next)
        
        expected_csp = "default-src 'self'; script-src 'self'; connect-src 'self'"
        self.assertEqual(result.headers["Content-Security-Policy"], expected_csp)
        
    @patch.dict(os.environ, {"CONTENT_SECURITY_POLICY": "default-src 'none'; script-src 'self'"})
    async def test_custom_csp_header(self):
        """Test that custom CSP header from env var is used."""
        request = self.create_mock_request("GET", "/api/test")
        response = self.create_mock_response(200)
        
        call_next = Mock(return_value=response)
        result = await self.middleware.dispatch(request, call_next)
        
        expected_csp = "default-src 'none'; script-src 'self'"
        self.assertEqual(result.headers["Content-Security-Policy"], expected_csp)
        
    @patch.dict(os.environ, {"ENABLE_HTTPS": "true"})
    async def test_hsts_header_when_https_enabled(self):
        """Test that HSTS header is added when HTTPS is enabled."""
        request = self.create_mock_request("GET", "/api/test")
        response = self.create_mock_response(200)
        
        call_next = Mock(return_value=response)
        result = await self.middleware.dispatch(request, call_next)
        
        expected_hsts = "max-age=31536000; includeSubDomains"
        self.assertEqual(result.headers["Strict-Transport-Security"], expected_hsts)
        
    @patch.dict(os.environ, {"ENABLE_HTTPS": "false"})
    async def test_no_hsts_header_when_https_disabled(self):
        """Test that HSTS header is not added when HTTPS is disabled."""
        request = self.create_mock_request("GET", "/api/test")
        response = self.create_mock_response(200)
        
        call_next = Mock(return_value=response)
        result = await self.middleware.dispatch(request, call_next)
        
        self.assertNotIn("Strict-Transport-Security", result.headers)
        
    async def test_hsts_header_default_behavior(self):
        """Test that HSTS header is not added by default (no env var)."""
        request = self.create_mock_request("GET", "/api/test")
        response = self.create_mock_response(200)
        
        # Ensure no HTTPS env var is set
        if "ENABLE_HTTPS" in os.environ:
            del os.environ["ENABLE_HTTPS"]
            
        call_next = Mock(return_value=response)
        result = await self.middleware.dispatch(request, call_next)
        
        self.assertNotIn("Strict-Transport-Security", result.headers)


if __name__ == '__main__':
    # Import asyncio for async test support
    try:
        import asyncio
    except ImportError:
        pass
        
    unittest.main()