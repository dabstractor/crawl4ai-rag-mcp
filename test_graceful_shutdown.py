#!/usr/bin/env python3
"""
Test script for graceful shutdown functionality.

This script tests the graceful shutdown behavior by:
1. Starting the server in a subprocess
2. Sending a SIGTERM signal after a few seconds
3. Verifying that the server shuts down gracefully
"""
import asyncio
import subprocess
import signal
import time
import sys
import os


async def test_graceful_shutdown():
    """Test the graceful shutdown functionality."""
    print("Testing graceful shutdown functionality...")
    
    # Start the server as a subprocess
    server_process = subprocess.Popen(
        [sys.executable, "-m", "src.crawl4ai_mcp"],
        env={**os.environ, "TRANSPORT": "sse", "PORT": "8052", "ENABLE_HTTP_API": "true"},  # Use different port for testing
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    try:
        # Give the server a moment to start
        await asyncio.sleep(3)
        
        print(f"Server started with PID: {server_process.pid}")
        print("Checking if server is running...")
        
        # Check if the process is still running
        if server_process.poll() is not None:
            print("ERROR: Server failed to start!")
            stdout, stderr = server_process.communicate()
            print(f"Server output:\n{stdout}")
            return False
        
        print("Server is running. Testing SIGTERM signal...")
        
        # Send SIGTERM to test graceful shutdown
        server_process.send_signal(signal.SIGTERM)
        
        # Wait for the server to shutdown gracefully (max 35 seconds)
        try:
            stdout, _ = server_process.communicate(timeout=35)
            print(f"Server shut down gracefully. Return code: {server_process.returncode}")
            print(f"Server output:\n{stdout}")
            return True
        
        except subprocess.TimeoutExpired:
            print("Server did not shut down within timeout period")
            server_process.kill()  # Force kill if graceful shutdown failed
            stdout, _ = server_process.communicate()
            print(f"Server output:\n{stdout}")
            return False
    
    except Exception as e:
        print(f"Error during test: {e}")
        return False
    
    finally:
        # Ensure the process is terminated
        if server_process.poll() is None:
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()


async def test_sigint_shutdown():
    """Test SIGINT (Ctrl+C) graceful shutdown."""
    print("\nTesting SIGINT graceful shutdown...")
    
    # Start the server as a subprocess
    server_process = subprocess.Popen(
        [sys.executable, "-m", "src.crawl4ai_mcp"],
        env={**os.environ, "TRANSPORT": "sse", "PORT": "8053", "ENABLE_HTTP_API": "true"},  # Use different port for testing
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    try:
        # Give the server a moment to start
        await asyncio.sleep(3)
        
        print(f"Server started with PID: {server_process.pid}")
        
        # Check if the process is still running
        if server_process.poll() is not None:
            print("ERROR: Server failed to start!")
            stdout, stderr = server_process.communicate()
            print(f"Server output:\n{stdout}")
            return False
        
        print("Server is running. Testing SIGINT signal...")
        
        # Send SIGINT to test graceful shutdown
        server_process.send_signal(signal.SIGINT)
        
        # Wait for the server to shutdown gracefully
        try:
            stdout, _ = server_process.communicate(timeout=35)
            print(f"Server shut down gracefully. Return code: {server_process.returncode}")
            print(f"Server output:\n{stdout}")
            return True
        
        except subprocess.TimeoutExpired:
            print("Server did not shut down within timeout period")
            server_process.kill()
            stdout, _ = server_process.communicate()
            print(f"Server output:\n{stdout}")
            return False
    
    except Exception as e:
        print(f"Error during test: {e}")
        return False
    
    finally:
        # Ensure the process is terminated
        if server_process.poll() is None:
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()


async def main():
    """Run all shutdown tests."""
    print("=== Graceful Shutdown Test Suite ===\n")
    
    # Test SIGTERM
    sigterm_result = await test_graceful_shutdown()
    
    # Test SIGINT
    sigint_result = await test_sigint_shutdown()
    
    print("\n=== Test Results ===")
    print(f"SIGTERM test: {'PASSED' if sigterm_result else 'FAILED'}")
    print(f"SIGINT test: {'PASSED' if sigint_result else 'FAILED'}")
    
    if sigterm_result and sigint_result:
        print("\n✅ All graceful shutdown tests PASSED!")
        return 0
    else:
        print("\n❌ Some graceful shutdown tests FAILED!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)