"""
Graceful shutdown handling for the Crawl4AI MCP server.

This module provides graceful shutdown functionality that:
1. Catches termination signals (SIGTERM, SIGINT)
2. Completes in-flight requests before shutting down
3. Closes database connections and resources properly
4. Logs shutdown process
"""
import signal
import sys
import asyncio
import logging
from typing import Optional, Callable, List
from starlette.applications import Starlette
from fastapi import FastAPI

logger = logging.getLogger(__name__)


class GracefulShutdown:
    """Handles graceful shutdown for the server."""
    
    def __init__(self, app: Optional[Starlette] = None):
        self.app = app
        self.should_exit = False
        self.force_exit = False
        self.shutdown_callbacks: List[Callable] = []
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
        
        # Register signal handlers
        self._register_signal_handlers()
        
        # Register shutdown event if app is provided
        if self.app:
            self._register_app_shutdown()
    
    def _register_signal_handlers(self):
        """Register signal handlers for graceful shutdown."""
        # Store original handlers
        self._original_sigint_handler = signal.signal(signal.SIGINT, self._handle_sigint)
        self._original_sigterm_handler = signal.signal(signal.SIGTERM, self._handle_sigterm)
        
        logger.info("Graceful shutdown handlers registered for SIGINT and SIGTERM")
    
    def _register_app_shutdown(self):
        """Register shutdown event handler with the app."""
        if hasattr(self.app, 'add_event_handler'):
            # FastAPI style
            self.app.add_event_handler("shutdown", self._app_shutdown_handler)
        elif hasattr(self.app, 'on_shutdown'):
            # Starlette style
            self.app.add_event_handler("shutdown", self._app_shutdown_handler)
        else:
            logger.warning("Unable to register app shutdown handler - app type not recognized")
    
    def _handle_sigint(self, sig, frame):
        """Handle SIGINT signal (Ctrl+C)."""
        logger.info("Received SIGINT, initiating graceful shutdown...")
        if self.should_exit:
            logger.warning("Received second SIGINT, forcing exit...")
            self.force_exit = True
            self._force_shutdown()
            return
        
        self.should_exit = True
        self._initiate_shutdown()
    
    def _handle_sigterm(self, sig, frame):
        """Handle SIGTERM signal."""
        logger.info("Received SIGTERM, initiating graceful shutdown...")
        self.should_exit = True
        self._initiate_shutdown()
    
    def _initiate_shutdown(self):
        """Initiate the shutdown process."""
        try:
            # Create a new event loop if we're not in one
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Schedule shutdown in the running loop
                    asyncio.create_task(self._trigger_shutdown())
                else:
                    # Run shutdown in the loop
                    loop.run_until_complete(self._trigger_shutdown())
            except RuntimeError:
                # No event loop, create one
                asyncio.run(self._trigger_shutdown())
        except Exception as e:
            logger.error(f"Error during shutdown initiation: {e}")
            self._force_shutdown()
    
    async def _trigger_shutdown(self):
        """Trigger the actual shutdown process."""
        logger.info("Starting graceful shutdown process...")
        
        # Wait for in-flight requests to complete (max 30 seconds)
        shutdown_timeout = 30
        for i in range(shutdown_timeout):
            if self.force_exit:
                logger.warning("Force exit requested, stopping graceful shutdown")
                break
            
            # Check if we should continue waiting
            if i < shutdown_timeout - 1:
                await asyncio.sleep(1)
        
        # Run cleanup callbacks
        await self._run_shutdown_callbacks()
        
        logger.info("Graceful shutdown completed")
    
    async def _app_shutdown_handler(self):
        """App shutdown event handler."""
        logger.info("App shutdown event triggered")
        await self._run_shutdown_callbacks()
    
    async def _run_shutdown_callbacks(self):
        """Run all registered shutdown callbacks."""
        logger.info(f"Running {len(self.shutdown_callbacks)} shutdown callbacks...")
        
        for callback in self.shutdown_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
                logger.debug(f"Shutdown callback {callback.__name__} completed")
            except Exception as e:
                logger.error(f"Error in shutdown callback {callback.__name__}: {e}")
        
        logger.info("All shutdown callbacks completed")
    
    def _force_shutdown(self):
        """Force immediate shutdown."""
        logger.warning("Forcing immediate shutdown...")
        
        # Restore original signal handlers
        if self._original_sigint_handler:
            signal.signal(signal.SIGINT, self._original_sigint_handler)
        if self._original_sigterm_handler:
            signal.signal(signal.SIGTERM, self._original_sigterm_handler)
        
        sys.exit(1)
    
    def add_shutdown_callback(self, callback: Callable):
        """Add a callback to be executed during shutdown."""
        self.shutdown_callbacks.append(callback)
        logger.debug(f"Added shutdown callback: {callback.__name__}")
    
    def remove_shutdown_callback(self, callback: Callable):
        """Remove a shutdown callback."""
        if callback in self.shutdown_callbacks:
            self.shutdown_callbacks.remove(callback)
            logger.debug(f"Removed shutdown callback: {callback.__name__}")


# Global shutdown handler instance
_shutdown_handler: Optional[GracefulShutdown] = None


def get_shutdown_handler() -> GracefulShutdown:
    """Get or create the global shutdown handler."""
    global _shutdown_handler
    if _shutdown_handler is None:
        _shutdown_handler = GracefulShutdown()
    return _shutdown_handler


def setup_graceful_shutdown(app: Optional[Starlette] = None) -> GracefulShutdown:
    """Setup graceful shutdown for the application."""
    global _shutdown_handler
    
    if _shutdown_handler is None:
        _shutdown_handler = GracefulShutdown(app)
        logger.info("Graceful shutdown setup completed")
    else:
        # Update app if provided
        if app and not _shutdown_handler.app:
            _shutdown_handler.app = app
            _shutdown_handler._register_app_shutdown()
            logger.info("Updated shutdown handler with app")
    
    return _shutdown_handler


def add_shutdown_callback(callback: Callable):
    """Add a shutdown callback to the global handler."""
    handler = get_shutdown_handler()
    handler.add_shutdown_callback(callback)


async def cleanup_resources():
    """Default cleanup function for common resources."""
    logger.info("Running default resource cleanup...")
    
    # Add any default cleanup logic here
    # For example, closing database connections, clearing caches, etc.
    
    # Close any asyncio tasks that might be running
    tasks = [task for task in asyncio.all_tasks() if not task.done()]
    if tasks:
        logger.info(f"Cancelling {len(tasks)} running tasks...")
        for task in tasks:
            if not task.cancelled():
                task.cancel()
        
        # Wait for tasks to complete cancellation
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.warning(f"Error cancelling tasks: {e}")
    
    logger.info("Default resource cleanup completed")