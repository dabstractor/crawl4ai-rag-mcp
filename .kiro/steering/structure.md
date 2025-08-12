# Project Structure

## Root Directory Organization

```
├── src/                    # Main application code
├── knowledge_graphs/       # Neo4j knowledge graph modules
├── ui-project/            # Web UI for visualizing crawled content
├── searxng/               # SearXNG configuration
├── .kiro/                 # Kiro IDE configuration and specs
├── .taskmaster/           # Task Master project management
├── docker-compose.yml     # Complete stack deployment
├── Dockerfile             # MCP server container
├── pyproject.toml         # Python dependencies
└── crawled_pages.sql      # PostgreSQL schema
```

## Source Code Structure (`src/`)

```
src/
├── crawl4ai_mcp.py        # Main MCP server with FastMCP
├── config.py              # Environment configuration
├── utils.py               # Core utilities (Supabase, RAG)
├── postgresql_adapter.py  # PostgreSQL integration
├── api/                   # HTTP REST API
│   ├── endpoints.py       # FastAPI route handlers
│   └── responses.py       # Pydantic response models
└── utils/                 # Additional utilities
    └── http_helpers.py    # HTTP API helper functions
```

## Knowledge Graph Modules (`knowledge_graphs/`)

```
knowledge_graphs/
├── parse_repo_into_neo4j.py      # GitHub repo → Neo4j parser
├── ai_script_analyzer.py         # Python AST analysis
├── knowledge_graph_validator.py  # Hallucination detection
├── hallucination_reporter.py     # Report generation
└── query_knowledge_graph.py      # Graph querying
```

## Configuration Files

- **`.env`**: Environment variables (API keys, database URLs)
- **`docker-compose.yml`**: Multi-service container orchestration
- **`pyproject.toml`**: Python project metadata and dependencies
- **`crawled_pages.sql`**: PostgreSQL schema with pgvector

## Key Conventions

### File Naming
- Snake_case for Python modules
- Kebab-case for Docker/config files
- PascalCase for classes
- lowercase for directories

### Code Organization
- MCP tools defined with `@mcp.tool()` decorators
- HTTP endpoints in `src/api/endpoints.py`
- Utilities separated by concern (database, HTTP, RAG)
- Async/await for all I/O operations

### Docker Structure
- Multi-stage builds for optimization
- Health checks for service dependencies
- Named volumes for data persistence
- Internal networks for service communication

### Environment Management
- `.env.example` template for required variables
- Environment-specific overrides supported
- Validation in `config.py` with sensible defaults