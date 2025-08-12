# Technology Stack

## Core Technologies

- **Python 3.12+**: Main application language
- **FastMCP**: MCP server framework with SSE/HTTP support
- **FastAPI**: HTTP REST API endpoints for browser clients
- **Crawl4AI 0.6.2**: Web crawling and content extraction
- **SearXNG**: Private search engine integration
- **PostgreSQL + pgvector**: Vector database for embeddings
- **Neo4j**: Knowledge graph for AI hallucination detection
- **Docker Compose**: Complete containerized deployment

## Key Dependencies

```toml
crawl4ai==0.6.2
mcp==1.7.1
supabase==2.15.1
openai==1.71.0
sentence-transformers>=4.1.0
neo4j>=5.28.1
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
```

## Architecture Patterns

- **MCP Protocol**: Both SSE and stdio transport support
- **Dual API**: MCP tools + HTTP REST endpoints
- **RAG Pipeline**: Chunking → Embedding → Vector Search → Reranking
- **Async/Await**: All I/O operations are asynchronous
- **Context Management**: Lifespan management for resources
- **Microservices**: Containerized services with Docker Compose

## Common Commands

### Development
```bash
# Start complete stack
docker compose up -d

# View logs
docker compose logs -f mcp-crawl4ai

# Restart specific service
docker compose restart mcp-crawl4ai

# Stop everything
docker compose down
```

### Testing
```bash
# Test HTTP API
python test_http_api.py

# Test error handling
python test_error_handling.py

# Health check
curl http://localhost:8051/health
```

### Database Setup
```bash
# Initialize PostgreSQL with pgvector
# SQL schema is in crawled_pages.sql
# Auto-loaded via docker-entrypoint-initdb.d
```

## Environment Configuration

Key environment variables in `.env`:
- `OPENAI_API_KEY`: Required for embeddings
- `SUPABASE_URL/SUPABASE_SERVICE_KEY`: Vector database
- `NEO4J_URI/NEO4J_USER/NEO4J_PASSWORD`: Knowledge graph
- `USE_*` flags: Enable RAG enhancement strategies