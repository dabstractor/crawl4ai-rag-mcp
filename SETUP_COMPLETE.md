# 🐳 Self-Contained Crawl4AI RAG MCP Server - READY TO USE!

## 🎯 What You Now Have

A **completely self-contained** Crawl4AI RAG MCP Server that includes:
- **PostgreSQL with pgvector** (local database, replaces Supabase)
- **SearXNG** (local search engine)
- **Crawl4AI MCP Server** (web crawling and RAG)
- **Caddy Reverse Proxy** (for HTTPS support)
- **Valkey** (Redis alternative for caching)

**Everything runs locally in Docker containers - no external services required!**

## 🚀 Quick Start (3 Steps)

### 1. Add Your OpenAI API Key
```bash
nano .env
# Add your OpenAI API key to the OPENAI_API_KEY line
```

### 2. Start Everything
```bash
./start.sh
```

### 3. Connect to Claude Code
```bash
claude mcp add-json crawl4ai-rag '{"type":"http","url":"http://localhost:8051/sse"}' --scope user
```

## 📋 Service Details

| Service | Port | Purpose |
|---------|------|---------|
| MCP Server | 8051 | Main MCP interface for AI agents |
| SearXNG | 8080 | Local search engine |
| PostgreSQL | 54321 | Vector database for RAG |

**All ports are localhost-only for security!**

## 🛠️ Management Commands

```bash
# Start all services
./start.sh

# Stop all services  
./stop.sh

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Rebuild after changes
docker-compose up -d --build
```

## 🔧 Configuration

Current RAG settings (in `.env`):
- ✅ **Hybrid Search**: Combines vector + keyword search
- ✅ **Reranking**: Improves result relevance
- ❌ **Contextual Embeddings**: Disabled (can enable for higher quality)
- ❌ **Agentic RAG**: Disabled (can enable for code examples)
- ❌ **Knowledge Graph**: Disabled (requires Neo4j)

## 🎯 Available MCP Tools

Once connected to Claude Code, you'll have:

1. **`crawl_single_page`** - Crawl and index a single webpage
2. **`smart_crawl_url`** - Intelligently crawl entire websites/documentation
3. **`perform_rag_query`** - Search through crawled content
4. **`get_available_sources`** - List all indexed sources
5. **`search_web`** - Search the web using local SearXNG

## 🔍 Usage Examples

Ask Claude Code:
- *"Use smart_crawl_url to crawl and index https://docs.fastapi.tiangolo.com"*
- *"Search the crawled content for FastAPI authentication examples"*  
- *"Search the web for recent Python tutorials"*

## 🛡️ Security Features

- All services run in isolated Docker containers
- No external dependencies except OpenAI API for embeddings
- All ports bound to localhost only
- Data persisted in Docker volumes
- Can be completely stopped/started on demand

## 📊 Resource Usage

- **Disk**: ~2GB for images + your crawled data
- **Memory**: ~1-2GB when running
- **Network**: Only outbound for OpenAI API and web crawling

## 🔧 Troubleshooting

**Container won't start?**
```bash
docker-compose logs mcp-crawl4ai
```

**Database connection issues?**  
```bash
docker-compose logs postgres
```

**Need to reset everything?**
```bash
./stop.sh
docker-compose down -v  # Removes all data
./start.sh
```

**OpenAI API errors?**
- Check your API key in `.env`
- Verify you have credits in your OpenAI account

## 🎉 You're All Set!

This is now a **completely self-contained** solution that:
- ✅ Starts/stops on demand
- ✅ No external service dependencies (except OpenAI for embeddings)
- ✅ Includes local database and search engine
- ✅ Works with any MCP-compatible AI assistant
- ✅ Preserves data between restarts

Just add your OpenAI API key and run `./start.sh`!
