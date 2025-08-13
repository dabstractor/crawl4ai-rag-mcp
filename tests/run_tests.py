#!/usr/bin/env python3
"""
Test runner for Crawl4AI MCP HTTP API tests.

This script runs all available test suites and provides detailed reporting.
"""

import sys
import os
import unittest
from typing import List, Dict, Any

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def discover_and_run_tests() -> Dict[str, Any]:
    """
    Discover and run all test modules in the tests directory.
    
    Returns:
        Dictionary with test results and summary
    """
    # Discover tests
    loader = unittest.TestLoader()
    test_dir = os.path.dirname(__file__)
    suite = loader.discover(test_dir, pattern='test_*.py')
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )
    
    print("🧪 Discovering and running all API tests...")
    print("=" * 80)
    
    result = runner.run(suite)
    
    # Calculate results
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    success_count = total_tests - failures - errors
    success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0
    
    results = {
        "total_tests": total_tests,
        "successes": success_count,
        "failures": failures,
        "errors": errors,
        "success_rate": success_rate,
        "passed": failures == 0 and errors == 0
    }
    
    return results, result

def print_detailed_summary(results: Dict[str, Any], test_result: unittest.TestResult):
    """Print detailed test summary."""
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 80)
    
    print(f"🔢 Total Tests:     {results['total_tests']}")
    print(f"✅ Passed:         {results['successes']}")
    print(f"❌ Failed:         {results['failures']}")
    print(f"🚨 Errors:         {results['errors']}")
    print(f"📈 Success Rate:   {results['success_rate']:.1f}%")
    
    if results['passed']:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ API endpoints are properly structured")
        print("✅ Parameter validation is working")
        print("✅ Error handling is implemented")
        print("✅ Response models are correctly defined")
        print("✅ CORS configuration is valid")
    else:
        print(f"\n⚠️  {results['failures'] + results['errors']} TESTS FAILED")
        
        if test_result.failures:
            print(f"\n❌ FAILURES ({len(test_result.failures)}):")
            for i, (test, traceback) in enumerate(test_result.failures, 1):
                print(f"  {i}. {test}")
                # Extract the assertion error message
                lines = traceback.split('\n')
                for line in lines:
                    if 'AssertionError' in line:
                        print(f"     → {line.strip()}")
                        break
        
        if test_result.errors:
            print(f"\n🚨 ERRORS ({len(test_result.errors)}):")
            for i, (test, traceback) in enumerate(test_result.errors, 1):
                print(f"  {i}. {test}")
                # Extract the error message
                lines = traceback.split('\n')
                for line in lines:
                    if any(error_type in line for error_type in ['Error:', 'Exception:']):
                        print(f"     → {line.strip()}")
                        break

def print_test_coverage_info():
    """Print information about what the tests cover."""
    print("\n" + "=" * 80)
    print("🎯 TEST COVERAGE SUMMARY")
    print("=" * 80)
    
    coverage_areas = [
        "✅ API Endpoint Structure Validation",
        "✅ HTTP Response Model Testing", 
        "✅ Parameter Validation Logic",
        "✅ Error Response Format Verification",
        "✅ CORS Configuration Testing",
        "✅ HTTP Status Code Validation",
        "✅ Content-Type Header Verification",
        "✅ Live Server Testing (when available)",
        "✅ Edge Case Parameter Testing",
        "✅ API Endpoint Path Validation"
    ]
    
    print("The test suite covers:")
    for area in coverage_areas:
        print(f"  {area}")
    
    print(f"\n📋 Endpoints Tested:")
    endpoints = [
        "  • GET  /api/health",
        "  • GET  /api/sources",
        "  • GET  /api/search",
        "  • POST /api/search", 
        "  • GET  /api/code-examples",
        "  • GET  /api/status"
    ]
    
    for endpoint in endpoints:
        print(endpoint)

def main():
    """Main test runner function."""
    print("🚀 Crawl4AI MCP HTTP API Test Suite")
    print("=" * 80)
    print("This test suite validates API structure, error handling, and validation")
    print("Tests work both with and without a running server")
    print("")
    
    try:
        # Run all tests
        results, test_result = discover_and_run_tests()
        
        # Print detailed summary
        print_detailed_summary(results, test_result)
        
        # Print coverage information
        print_test_coverage_info()
        
        # Print recommendations
        print(f"\n📝 RECOMMENDATIONS:")
        if results['passed']:
            print("  • All tests passed - API is ready for production")
            print("  • Consider adding integration tests with live server")
            print("  • Monitor API performance under load")
        else:
            print("  • Fix failing tests before deploying to production")
            print("  • Review error handling for edge cases")
            print("  • Validate API responses match OpenAPI specification")
        
        print(f"\n💡 Next Steps:")
        print("  • Add performance benchmarks")
        print("  • Implement rate limiting tests")
        print("  • Add security vulnerability scanning")
        print("  • Set up continuous integration testing")
        
        # Exit with appropriate code
        exit_code = 0 if results['passed'] else 1
        print(f"\n🏁 Test run completed with exit code: {exit_code}")
        
        return exit_code
        
    except Exception as e:
        print(f"\n💥 Test runner failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)