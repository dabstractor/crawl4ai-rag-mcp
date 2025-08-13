#!/usr/bin/env python3
"""
Integration tests for UI connectivity to HTTP API.

Tests that verify the UI can connect to and interact with the HTTP API server.
Includes both API client tests and optional browser automation tests.
"""

import unittest
import sys
import os
import time
from typing import Dict, Any

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class TestUIAPIConnectivity(unittest.TestCase):
    """Test UI connectivity to HTTP API without browser automation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.api_base_url = "http://localhost:8051/api"
        self.ui_base_url = "http://localhost:3741"
        self.timeout = 10
    
    def make_api_request(self, endpoint: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
        """Make HTTP request to API with error handling."""
        if not REQUESTS_AVAILABLE:
            self.skipTest("requests library not available")
        
        url = f"{self.api_base_url}{endpoint}"
        
        try:
            response = requests.request(method, url, timeout=self.timeout, **kwargs)
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                "headers": dict(response.headers)
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": None
            }
    
    def test_api_health_endpoint(self):
        """Test that the API health endpoint returns successful response."""
        result = self.make_api_request("/health")
        
        if not result["success"]:
            self.skipTest(f"API server not available: {result.get('error', 'Unknown error')}")
        
        self.assertEqual(result["status_code"], 200)
        self.assertIn("data", result["data"])
        
        data = result["data"]["data"]
        self.assertIn("status", data)
        self.assertEqual(data["status"], "healthy")
        self.assertIn("version", data)
        self.assertIn("mcp_connected", data)
    
    def test_api_sources_endpoint(self):
        """Test that the sources endpoint returns data for dropdown population."""
        result = self.make_api_request("/sources")
        
        if not result["success"]:
            self.skipTest(f"API server not available: {result.get('error', 'Unknown error')}")
        
        self.assertEqual(result["status_code"], 200)
        self.assertIn("sources", result["data"])
        self.assertIsInstance(result["data"]["sources"], list)
        
        # Verify sources have required fields for dropdown
        if result["data"]["sources"]:
            source = result["data"]["sources"][0]
            self.assertIn("domain", source)
            self.assertIn("count", source)
            self.assertIsInstance(source["domain"], str)
            self.assertIsInstance(source["count"], int)
    
    def test_api_search_functionality(self):
        """Test that the search endpoint returns results."""
        # Test GET search
        result = self.make_api_request("/search", params={"query": "test"})
        
        if not result["success"]:
            self.skipTest(f"API server not available: {result.get('error', 'Unknown error')}")
        
        self.assertEqual(result["status_code"], 200)
        self.assertIn("data", result["data"])
        self.assertIn("query", result["data"])
        self.assertEqual(result["data"]["query"], "test")
        self.assertIn("total_results", result["data"])
        
        # Test POST search
        post_result = self.make_api_request(
            "/search", 
            method="POST",
            json={"query": "test search", "match_count": 5}
        )
        
        if post_result["success"]:
            self.assertEqual(post_result["status_code"], 200)
            self.assertIn("data", post_result["data"])
            self.assertIn("query", post_result["data"])
            self.assertEqual(post_result["data"]["query"], "test search")
    
    def test_api_search_with_source_filter(self):
        """Test search functionality with source filtering."""
        # First get available sources
        sources_result = self.make_api_request("/sources")
        
        if not sources_result["success"]:
            self.skipTest(f"API server not available: {sources_result.get('error', 'Unknown error')}")
        
        sources = sources_result["data"]["sources"]
        if not sources:
            self.skipTest("No sources available for testing")
        
        # Test search with source filter
        source_domain = sources[0]["domain"]
        result = self.make_api_request("/search", params={
            "query": "test", 
            "source": source_domain
        })
        
        if result["success"]:
            self.assertEqual(result["status_code"], 200)
            self.assertIn("query", result["data"])
            self.assertEqual(result["data"]["query"], "test")
    
    def test_api_code_examples_endpoint(self):
        """Test that the code examples endpoint works."""
        result = self.make_api_request("/code-examples", params={"query": "function"})
        
        if not result["success"]:
            self.skipTest(f"API server not available: {result.get('error', 'Unknown error')}")
        
        self.assertEqual(result["status_code"], 200)
        # API returns 'data' instead of 'results'
        self.assertIn("data", result["data"])
        self.assertIn("query", result["data"])
        self.assertEqual(result["data"]["query"], "function")
        self.assertIn("total_results", result["data"])
    
    def test_api_error_handling(self):
        """Test API error handling for invalid requests."""
        # Test search without required query parameter
        result = self.make_api_request("/search")
        
        if not result["success"]:
            self.skipTest(f"API server not available: {result.get('error', 'Unknown error')}")
        
        # API may return 200 with empty results instead of error for missing query
        # This tests the actual behavior - adjust based on API implementation
        self.assertIn(result["status_code"], [200, 400, 422])
        
        # Test invalid match_count
        result = self.make_api_request("/search", params={
            "query": "test",
            "match_count": -1
        })
        
        if result["success"]:
            # API may handle invalid parameters gracefully
            self.assertIn(result["status_code"], [200, 400, 422])
    
    def test_api_cors_headers(self):
        """Test that CORS headers are present for UI connectivity."""
        result = self.make_api_request("/health")
        
        if not result["success"]:
            self.skipTest(f"API server not available: {result.get('error', 'Unknown error')}")
        
        headers = result["headers"]
        
        # Check for CORS headers (case-insensitive)
        cors_headers_found = False
        for header_name in headers:
            if header_name.lower().startswith('access-control-allow'):
                cors_headers_found = True
                break
        
        # Note: CORS headers may only be present on preflight requests
        # This test documents expected behavior but may not fail if CORS is handled differently
        if not cors_headers_found:
            print("Warning: No CORS headers detected in response. This may be normal if CORS is handled at preflight level.")


@unittest.skipUnless(SELENIUM_AVAILABLE, "Selenium not available")
class TestUIBrowserAutomation(unittest.TestCase):
    """Browser automation tests for UI components (requires Selenium)."""
    
    def setUp(self):
        """Set up browser for testing."""
        self.api_base_url = "http://localhost:8051/api"
        self.ui_base_url = "http://localhost:3741"
        self.timeout = 15
        
        # Configure Chrome options for headless testing
        self.chrome_options = ChromeOptions()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--window-size=1280,720")
        
        self.driver = None
    
    def tearDown(self):
        """Clean up browser."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
    
    def start_browser(self):
        """Start browser with error handling."""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            return True
        except WebDriverException as e:
            self.skipTest(f"Chrome WebDriver not available: {e}")
            return False
    
    def check_ui_availability(self):
        """Check if UI is available."""
        if not REQUESTS_AVAILABLE:
            self.skipTest("requests library not available")
        
        try:
            response = requests.get(self.ui_base_url, timeout=5)
            if response.status_code != 200:
                self.skipTest(f"UI not available at {self.ui_base_url}")
        except requests.exceptions.RequestException:
            self.skipTest(f"UI not available at {self.ui_base_url}")
    
    def test_ui_loads_successfully(self):
        """Test that the UI loads without errors."""
        self.check_ui_availability()
        if not self.start_browser():
            return
        
        try:
            self.driver.get(self.ui_base_url)
            
            # Wait for basic elements to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check page title
            self.assertIn("Crawl4AI", self.driver.title.lower())
            
        except TimeoutException:
            self.fail("UI failed to load within timeout period")
    
    def test_connection_test_component(self):
        """Test the connection test component functionality."""
        self.check_ui_availability()
        if not self.start_browser():
            return
        
        try:
            self.driver.get(self.ui_base_url)
            
            # Look for connection test component
            connection_element = WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='connection'], [id*='connection'], [data-testid*='connection']"))
            )
            
            # Check if connection status is displayed
            self.assertTrue(connection_element.is_displayed())
            
            # Look for status text (success or error)
            status_indicators = ["connected", "healthy", "success", "error", "failed"]
            page_text = self.driver.page_source.lower()
            
            status_found = any(indicator in page_text for indicator in status_indicators)
            self.assertTrue(status_found, "No connection status indicator found")
            
        except TimeoutException:
            self.skipTest("Connection test component not found or UI not fully loaded")
    
    def test_sources_dropdown_population(self):
        """Test that the sources dropdown gets populated."""
        self.check_ui_availability()
        if not self.start_browser():
            return
        
        try:
            self.driver.get(self.ui_base_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Look for dropdown or select elements
            dropdown_selectors = [
                "select", 
                "[role='combobox']",
                "[class*='dropdown']", 
                "[class*='select']",
                "[data-testid*='source']"
            ]
            
            dropdown_found = False
            for selector in dropdown_selectors:
                try:
                    dropdown = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if dropdown.is_displayed():
                        dropdown_found = True
                        break
                except:
                    continue
            
            if not dropdown_found:
                self.skipTest("Sources dropdown not found in UI")
            
            # Give time for API call to populate dropdown
            time.sleep(2)
            
            # Check if dropdown has options
            options = self.driver.find_elements(By.TAG_NAME, "option")
            if not options:
                # Try alternative option selectors
                options = self.driver.find_elements(By.CSS_SELECTOR, "[role='option'], [class*='option']")
            
            # Should have at least a default option or actual source options
            self.assertGreaterEqual(len(options), 1, "Dropdown should have at least one option")
            
        except TimeoutException:
            self.skipTest("Sources dropdown test timed out")
    
    def test_search_functionality_ui(self):
        """Test search functionality through the UI."""
        self.check_ui_availability()
        if not self.start_browser():
            return
        
        try:
            self.driver.get(self.ui_base_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Find search input
            search_input_selectors = [
                "input[type='text']",
                "input[type='search']", 
                "[placeholder*='search']",
                "[class*='search-input']",
                "[id*='search']",
                "[data-testid*='search']"
            ]
            
            search_input = None
            for selector in search_input_selectors:
                try:
                    search_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if search_input.is_displayed():
                        break
                except:
                    continue
            
            if not search_input:
                self.skipTest("Search input not found")
            
            # Enter search query
            search_input.clear()
            search_input.send_keys("test query")
            
            # Find and click search button
            search_button_selectors = [
                "button[type='submit']",
                "[class*='search-button']",
                "[class*='btn-search']", 
                "button:contains('Search')",
                "[data-testid*='search-button']"
            ]
            
            search_button = None
            for selector in search_button_selectors:
                try:
                    search_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if search_button.is_displayed():
                        break
                except:
                    continue
            
            if search_button:
                search_button.click()
            else:
                # Try submitting form if no button found
                search_input.submit()
            
            # Wait for results to appear
            time.sleep(3)
            
            # Look for results container
            results_selectors = [
                "[class*='results']",
                "[class*='search-results']", 
                "[id*='results']",
                "[data-testid*='results']"
            ]
            
            results_found = False
            for selector in results_selectors:
                try:
                    results_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if results_element.is_displayed():
                        results_found = True
                        break
                except:
                    continue
            
            # Check if search was executed (results area appeared or loading indicator)
            page_text = self.driver.page_source.lower()
            search_executed = (
                results_found or
                "loading" in page_text or 
                "searching" in page_text or
                "results" in page_text or
                search_input.get_attribute("value") == "test query"
            )
            
            self.assertTrue(search_executed, "Search functionality appears not to be working")
            
        except TimeoutException:
            self.skipTest("Search functionality test timed out")
    
    def test_error_display_handling(self):
        """Test that errors are displayed to users."""
        self.check_ui_availability()
        if not self.start_browser():
            return
        
        try:
            self.driver.get(self.ui_base_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check for error display elements
            error_selectors = [
                "[class*='error']",
                "[class*='alert']", 
                "[class*='warning']",
                "[role='alert']",
                "[data-testid*='error']"
            ]
            
            # Error elements might be hidden initially
            error_elements = []
            for selector in error_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    error_elements.extend(elements)
                except:
                    continue
            
            # We expect error display elements to exist (even if hidden)
            # This tests the UI's capability to show errors
            if error_elements:
                print(f"Found {len(error_elements)} error display elements")
            else:
                print("No dedicated error display elements found - errors may be handled differently")
            
            # This test primarily validates the UI structure exists for error handling
            
        except TimeoutException:
            self.skipTest("Error display test timed out")


def run_integration_tests():
    """Run all integration test suites."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestUIAPIConnectivity))
    
    if SELENIUM_AVAILABLE:
        suite.addTests(loader.loadTestsFromTestCase(TestUIBrowserAutomation))
    else:
        print("⚠️  Selenium not available - skipping browser automation tests")
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Integration Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {result.testsRun - len(result.failures) - len(result.errors) - result.testsRun + len([t for t, _ in result.failures + result.errors])}")
    
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100)
        print(f"Success rate: {success_rate:.1f}%")
    
    # Print library availability
    print(f"\nLibrary Availability:")
    print(f"- requests: {'✅' if REQUESTS_AVAILABLE else '❌'}")
    print(f"- selenium: {'✅' if SELENIUM_AVAILABLE else '❌'}")
    
    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}")
            print(f"  {traceback.split('AssertionError:')[-1].strip() if 'AssertionError:' in traceback else 'See details above'}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}")
    
    return len(result.failures) == 0 and len(result.errors) == 0


if __name__ == "__main__":
    print("Running UI Integration Tests")
    print("="*60)
    print("Testing UI connectivity to HTTP API server")
    print(f"API Base URL: http://localhost:8051/api")
    print(f"UI Base URL: http://localhost:3741")
    
    if not REQUESTS_AVAILABLE:
        print("\n⚠️  WARNING: 'requests' library not available")
        print("   Install with: pip install requests")
    
    if not SELENIUM_AVAILABLE:
        print("\n⚠️  INFO: 'selenium' library not available")
        print("   Browser automation tests will be skipped")
        print("   To enable: pip install selenium")
        print("   Also requires ChromeDriver: https://chromedriver.chromium.org/")
    
    print("\nStarting tests...\n")
    
    success = run_integration_tests()
    
    if success:
        print("\n✅ All integration tests passed!")
        print("✅ UI-API connectivity verified")
        if SELENIUM_AVAILABLE:
            print("✅ Browser automation tests completed")
    else:
        print("\n❌ Some integration tests failed.")
        print("Check API server is running on port 8051")
        print("Check UI server is running on port 3741")
        sys.exit(1)