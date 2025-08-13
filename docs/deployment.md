# Crawl4AI MCP HTTP API Deployment Guide

## System Requirements

- Python 3.9 or higher
- Docker and Docker Compose (for containerized deployment)
- 4GB RAM minimum (8GB recommended)
- 20GB disk space
- Internet connectivity for initial setup and dependency installation

## Installation

### Docker Deployment (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/crawl4ai-mcp.git
   cd crawl4ai-mcp
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Build and start the containers:
   ```bash
   docker-compose up -d
   ```

4. Verify the deployment:
   ```bash
   curl http://localhost:8051/api/health
   ```

### Manual Deployment

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/crawl4ai-mcp.git
   cd crawl4ai-mcp
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Start the server:
   ```bash
   python -m src.crawl4ai_mcp
   ```

## Configuration Options

### Environment Variables

#### Core Server Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `TRANSPORT` | MCP transport protocol (sse or stdio) | `sse` |
| `HOST` | Host to bind the server | `0.0.0.0` |
| `PORT` | Port to bind the server | `8051` |
| `OPENAI_API_KEY` | OpenAI API key for embeddings | `` |
| `MODEL_CHOICE` | LLM for summaries and embeddings | `gpt-4.1-nano-2025-04-14` |

#### HTTP API Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_HTTP_API` | Enable HTTP API endpoints | `true` |
| `CORS_ORIGINS` | Comma-separated list of allowed origins | `*` |
| `API_RATE_LIMIT` | Requests per minute per IP | `60` |
| `RATE_LIMIT_ENABLED` | Enable/disable rate limiting | `true` |
| `LOG_LEVEL` | Logging level | `info` |

#### SearXNG Integration
| Variable | Description | Default |
|----------|-------------|---------|
| `SEARXNG_URL` | SearXNG URL for search instances | `http://searxng:8080` |
| `SEARXNG_USER_AGENT` | User agent for SearXNG requests | `MCP-Crawl4AI-RAG-Server/1.0` |
| `SEARXNG_DEFAULT_ENGINES` | Default search engines | `google,bing,duckduckgo` |
| `SEARXNG_TIMEOUT` | Request timeout in seconds | `30` |

#### RAG Functionality
| Variable | Description | Default |
|----------|-------------|---------|
| `USE_CONTEXTUAL_EMBEDDINGS` | Enhance embeddings with context | `false` |
| `USE_HYBRID_SEARCH` | Combine vector + keyword search | `false` |
| `USE_AGENTIC_RAG` | Enable code example extraction | `false` |
| `USE_RERANKING` | Apply cross-encoder reranking | `false` |
| `USE_KNOWLEDGE_GRAPH` | Enable Neo4j knowledge graph tools | `false` |

#### Database Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `SUPABASE_URL` | PostgreSQL connection URL | `postgresql://crawl4ai_user:crawl4ai_secure_password_2024@postgres:5432/crawl4ai_rag` |
| `SUPABASE_SERVICE_KEY` | Database service key | `dummy_key_for_local_postgres` |

#### Neo4j Configuration (if USE_KNOWLEDGE_GRAPH=true)
| Variable | Description | Default |
|----------|-------------|---------|
| `NEO4J_URI` | Neo4j connection URI | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | `` |

## Security Considerations

1. **CORS Configuration**: In production, set specific allowed origins instead of using the wildcard `*`.
   ```bash
   # Example production CORS configuration
   CORS_ORIGINS=https://your-ui-domain.com,https://your-api-domain.com
   ```

2. **Rate Limiting**: Adjust rate limits based on your expected traffic and server capacity.
   ```bash
   # Example high-capacity configuration
   API_RATE_LIMIT=200
   RATE_LIMIT_ENABLED=true
   ```

3. **API Keys**: Protect your API keys and rotate them regularly. Use environment variables or secret management.
   ```bash
   # Never commit API keys to version control
   OPENAI_API_KEY=sk-...
   ```

4. **Firewall Rules**: Configure firewall rules to restrict access to the API server.
   ```bash
   # Example ufw configuration
   ufw allow from YOUR_IP to any port 8051
   ufw deny 8051
   ```

5. **HTTPS**: Use HTTPS in production by configuring a reverse proxy like Nginx with SSL certificates.
   ```nginx
   # Example Nginx configuration
   server {
       listen 443 ssl;
       server_name your-domain.com;
       
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       
       location / {
           proxy_pass http://localhost:8051;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

6. **Authentication**: Consider adding authentication for API endpoints if exposing to public networks.

## Monitoring and Maintenance

### Logging

Logs are written to stdout/stderr and can be viewed with:
```bash
# Docker logs
docker-compose logs -f mcp-crawl4ai

# Manual deployment logs (if configured)
tail -f /path/to/logs/server.log
```

### Metrics

Prometheus metrics are available at:
```bash
http://localhost:8051/metrics
```

Additional metrics from individual services:
```bash
# PostgreSQL metrics
docker-compose exec postgres pg_isready

# SearXNG metrics
curl http://localhost:8080/stats
```

### Health Checks

Use the health endpoint for monitoring:
```bash
curl http://localhost:8051/api/health
```

For Docker health checks, the system automatically verifies:
- Server startup and API availability
- Database connectivity
- SearXNG connectivity

### Database Maintenance

Regular database maintenance tasks:
```bash
# Connect to PostgreSQL container
docker-compose exec postgres psql -U crawl4ai_user -d crawl4ai_rag

# Check database size
SELECT pg_size_pretty(pg_database_size('crawl4ai_rag'));

# Vacuum database (recommended weekly)
VACUUM ANALYZE;
```

### Backup and Restore

Backup database:
```bash
# Create backup
docker-compose exec postgres pg_dump -U crawl4ai_user crawl4ai_rag > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U crawl4ai_user crawl4ai_rag < backup.sql
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if the server is running:
     ```bash
     docker-compose ps
     ```
   - Verify port configuration:
     ```bash
     netstat -tlnp | grep 8051
     ```
   - Check firewall settings:
     ```bash
     ufw status
     ```

2. **CORS Errors**
   - Verify CORS_ORIGINS configuration in .env
   - Check browser console for specific CORS errors
   - Ensure CORS headers are being sent:
     ```bash
     curl -H "Origin: http://localhost:3000" -v http://localhost:8051/api/health
     ```

3. **Slow Response Times**
   - Check server resource usage:
     ```bash
     docker stats
     ```
   - Verify database connection pool settings
   - Consider increasing cache TTL:
     ```bash
     # In .env
     CACHE_TTL=600
     ```

4. **Out of Memory Errors**
   - Increase container memory limits in docker-compose.yml:
     ```yaml
     services:
       mcp-crawl4ai:
         # ...
         deploy:
           resources:
             limits:
               memory: 4G
     ```
   - Check for memory leaks
   - Optimize large response handling

5. **Database Connection Issues**
   - Verify PostgreSQL is running:
     ```bash
     docker-compose exec postgres pg_isready -U crawl4ai_user -d crawl4ai_rag
     ```
   - Check database credentials in .env
   - Ensure network connectivity between containers

6. **API Key Errors**
   - Verify OPENAI_API_KEY is set correctly
   - Check API key validity with OpenAI
   - Ensure API key has required permissions

### Debugging Commands

```bash
# Check all service statuses
docker-compose ps

# View container logs
docker-compose logs mcp-crawl4ai

# View recent logs with timestamps
docker-compose logs --since 1h mcp-crawl4ai

# Check system resources
docker stats

# Test API connectivity
curl -v http://localhost:8051/api/health

# Test database connectivity
docker-compose exec postgres pg_isready -U crawl4ai_user -d crawl4ai_rag

# Test SearXNG connectivity
curl -v http://localhost:8080
```

### Log Analysis

```bash
# Filter error logs
docker-compose logs mcp-crawl4ai | grep ERROR

# Filter warning logs
docker-compose logs mcp-crawl4ai | grep WARN

# Monitor real-time logs
docker-compose logs -f mcp-crawl4ai

# Search for specific patterns
docker-compose logs mcp-crawl4ai | grep "search_query"
```

## Performance Tuning

1. **Caching**: Adjust CACHE_TTL for optimal performance:
   ```bash
   CACHE_TTL=300  # 5 minutes
   ```

2. **Database**: Optimize PostgreSQL performance:
   ```bash
   # In docker-compose.yml, add PostgreSQL tuning options
   command: >
     postgres
     -c shared_buffers=512MB
     -c effective_cache_size=2GB
     -c maintenance_work_mem=256MB
   ```

3. **API Rate Limits**: Adjust based on capacity:
   ```bash
   API_RATE_LIMIT=200  # Higher limits for production
   ```

4. **Resource Allocation**: Allocate sufficient resources in Docker:
   ```yaml
   services:
     mcp-crawl4ai:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 4G
           reservations:
             cpus: '1'
             memory: 2G
   ```

## Upgrade Process

1. **Backup**: Always backup your data before upgrading:
   ```bash
   docker-compose exec postgres pg_dump -U crawl4ai_user crawl4ai_rag > backup-$(date +%F).sql
   ```

2. **Pull Latest Changes**:
   ```bash
   git pull origin main
   ```

3. **Update Dependencies**:
   ```bash
   docker-compose build --no-cache
   ```

4. **Apply Database Migrations** (if applicable):
   ```bash
   # Check for migration scripts in the repository
   ```

5. **Restart Services**:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

6. **Verify Deployment**:
   ```bash
   curl http://localhost:8051/api/health
   ```