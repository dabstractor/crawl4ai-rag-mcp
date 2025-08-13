FROM python:3.12-slim

ARG PORT=8051

WORKDIR /app

# Install system dependencies for health checks
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy the MCP server files
COPY . .

# Install packages directly to the system (no virtual environment)
# Combining commands to reduce Docker layers
RUN uv pip install --system -e . && \
    crawl4ai-setup

ENV PYTHONPATH=/app

# Set default environment variables for HTTP API
ENV ENABLE_HTTP_API=true
ENV LOG_LEVEL=info
ENV RATE_LIMIT_ENABLED=true

EXPOSE ${PORT}

# Health check for HTTP API
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

# Command to run the MCP server
CMD ["python", "src/crawl4ai_mcp.py"]
