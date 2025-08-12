"""
Environment configuration for Crawl4AI MCP HTTP API.

This module provides a flexible configuration system using environment variables
with sensible defaults and validation.
"""

import os
from typing import List, Optional
from dataclasses import dataclass, field

@dataclass
class APISettings:
    """API server configuration settings."""
    
    # Server settings
    host: str = field(default="0.0.0.0")
    port: int = field(default=8051)
    debug: bool = field(default=False)
    
    # CORS settings
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    
    # Rate limiting
    rate_limit_enabled: bool = field(default=True)
    rate_limit_requests: int = field(default=60)
    
    # Logging
    log_level: str = field(default="info")
    
    # Cache settings
    cache_ttl: int = field(default=300)
    
    # MCP settings
    mcp_timeout: int = field(default=30)
    
    def __post_init__(self):
        """Initialize settings from environment variables."""
        # Server settings
        self.host = os.getenv("API_HOST", self.host)
        self.port = int(os.getenv("API_PORT", str(self.port)))
        self.debug = os.getenv("API_DEBUG", "false").lower() == "true"
        
        # CORS settings
        cors_origins_env = os.getenv("CORS_ORIGINS")
        if cors_origins_env:
            if cors_origins_env.strip() == "*":
                self.cors_origins = ["*"]
            else:
                self.cors_origins = [origin.strip() for origin in cors_origins_env.split(",")]
        
        # Rate limiting
        self.rate_limit_enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        self.rate_limit_requests = int(os.getenv("RATE_LIMIT_REQUESTS", str(self.rate_limit_requests)))
        
        # Logging
        self.log_level = os.getenv("LOG_LEVEL", self.log_level).lower()
        
        # Cache settings
        self.cache_ttl = int(os.getenv("CACHE_TTL", str(self.cache_ttl)))
        
        # MCP settings
        self.mcp_timeout = int(os.getenv("MCP_TIMEOUT", str(self.mcp_timeout)))
        
        # Validate settings
        self._validate_settings()
    
    def _validate_settings(self):
        """Validate configuration values."""
        # Validate log level
        valid_log_levels = ["debug", "info", "warning", "error", "critical"]
        if self.log_level not in valid_log_levels:
            raise ValueError(f"Invalid log level: {self.log_level}. Must be one of {valid_log_levels}")
        
        # Validate port
        if not (1 <= self.port <= 65535):
            raise ValueError(f"Invalid port: {self.port}. Must be between 1 and 65535")
        
        # Validate rate limit requests
        if self.rate_limit_requests < 1:
            raise ValueError(f"Rate limit requests must be positive: {self.rate_limit_requests}")
        
        # Validate cache TTL
        if self.cache_ttl < 0:
            raise ValueError(f"Cache TTL cannot be negative: {self.cache_ttl}")
        
        # Validate MCP timeout
        if self.mcp_timeout < 1:
            raise ValueError(f"MCP timeout must be positive: {self.mcp_timeout}")

# Create settings instance
settings = APISettings()

def parse_cors_origins(origins_str: str) -> List[str]:
    """Parse CORS origins from string."""
    if origins_str.strip() == "*":
        return ["*"]
    return [origin.strip() for origin in origins_str.split(",")]

def configure_logging():
    """Configure logging based on settings."""
    import logging
    import os
    
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Map string log level to logging constant
    log_level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL
    }
    
    log_level = log_level_map.get(settings.log_level, logging.INFO)
    
    # Configure root logger with both file and console handlers
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(log_dir, "http_api.log"))
        ]
    )
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("fastapi").setLevel(log_level)
    logging.getLogger("mcp").setLevel(log_level)
    logging.getLogger("http_api").setLevel(log_level)

def get_config_info() -> dict:
    """Get configuration information for debugging."""
    return {
        "host": settings.host,
        "port": settings.port,
        "debug": settings.debug,
        "cors_origins": settings.cors_origins,
        "rate_limit_enabled": settings.rate_limit_enabled,
        "rate_limit_requests": settings.rate_limit_requests,
        "log_level": settings.log_level,
        "cache_ttl": settings.cache_ttl,
        "mcp_timeout": settings.mcp_timeout
    }

# Example usage function
def example_usage():
    """Example of how to use the configuration system."""
    print("API Configuration:")
    print(f"  Host: {settings.host}")
    print(f"  Port: {settings.port}")
    print(f"  Debug: {settings.debug}")
    print(f"  CORS Origins: {settings.cors_origins}")
    print(f"  Rate Limiting: {settings.rate_limit_enabled} ({settings.rate_limit_requests} requests)")
    print(f"  Log Level: {settings.log_level}")
    print(f"  Cache TTL: {settings.cache_ttl}s")
    print(f"  MCP Timeout: {settings.mcp_timeout}s")

if __name__ == "__main__":
    example_usage()