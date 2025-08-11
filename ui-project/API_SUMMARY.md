# Crawl4AI MCP Server API Summary

## Overview
The Crawl4AI MCP Server provides a comprehensive set of tools for web crawling, search, and RAG (Retrieval Augmented Generation) capabilities. The server is accessible via HTTP SSE transport at `http://localhost:8051/sse`.

## Available Tools

### Core Tools (Always Available)

1. **`search`** - Comprehensive search tool that integrates SearXNG search with scraping and RAG functionality
   - Searches SearXNG with provided query
   - Automatically scrapes all found URLs
   - Stores content in vector database
   - Returns either RAG-processed results or raw markdown content
   - Parameters: `query`, `return_raw_markdown`, `num_results`, `batch_size`, `max_concurrent`, `max_rag_workers`

2. **`scrape_urls`** - Scrape one or more URLs and store their content in the vector database
   - Supports both single URLs and lists of URLs for batch processing
   - Stores content as embedding chunks in Supabase/PostgreSQL
   - Parameters: `url` (string or list), `max_concurrent`, `batch_size`, `return_raw_markdown`

3. **`smart_crawl_url`** - Intelligently crawl a full website based on URL type
   - Automatically detects URL type (sitemap, text file, regular webpage)
   - Applies appropriate crawling method
   - Parameters: `url`, `max_depth`, `max_concurrent`, `chunk_size`, `return_raw_markdown`, `query`, `max_rag_workers`

4. **`get_available_sources`** - Get a list of all available sources (domains) in the database
   - Returns source information with summaries and statistics
   - No parameters required

5. **`perform_rag_query`** - Search for relevant content using semantic search
   - Queries vector database for content relevant to the query
   - Optionally filter by source domain
   - Parameters: `query`, `source`, `match_count`

### Conditional Tools

6. **`search_code_examples`** - Search specifically for code examples (requires `USE_AGENTIC_RAG=true`)
   - Searches vector database for code examples with summaries
   - Optionally filter by source_id
   - Parameters: `query`, `source_id`, `match_count`

### Knowledge Graph Tools (requires `USE_KNOWLEDGE_GRAPH=true`)

7. **`parse_github_repository`** - Parse a GitHub repository into a Neo4j knowledge graph
   - Extracts classes, methods, functions, and relationships
   - Parameters: `repo_url`

8. **`check_ai_script_hallucinations`** - Analyze Python scripts for AI hallucinations
   - Validates scripts against knowledge graph
   - Parameters: `script_path`

9. **`query_knowledge_graph`** - Explore and query the Neo4j knowledge graph
   - Commands: `repos`, `classes`, `methods`, custom Cypher queries
   - Parameters: `command`

## Database Schema

The system uses a PostgreSQL database with three main tables:

### 1. `crawled_pages`
- `id` (UUID) - Primary key
- `url` (TEXT) - Source URL
- `chunk_number` (INTEGER) - Chunk sequence number
- `content` (TEXT) - Markdown content
- `metadata` (JSONB) - Content metadata
- `source_id` (TEXT) - Domain identifier
- `embedding` (VECTOR) - Content embeddings

### 2. `code_examples` (when USE_AGENTIC_RAG=true)
- `id` (UUID) - Primary key
- `url` (TEXT) - Source URL
- `chunk_number` (INTEGER) - Chunk sequence number
- `content` (TEXT) - Code example content
- `summary` (TEXT) - AI-generated summary
- `metadata` (JSONB) - Content metadata
- `source_id` (TEXT) - Domain identifier
- `embedding` (VECTOR) - Content embeddings

### 3. `sources`
- `source_id` (TEXT) - Domain identifier (primary key)
- `summary` (TEXT) - Domain summary
- `total_words` (INTEGER) - Word count
- `created_at` (TIMESTAMP) - Creation timestamp
- `updated_at` (TIMESTAMP) - Last update timestamp

## Stored Procedures

### `match_crawled_pages(query_embedding, match_count, source_filter)`
Performs vector similarity search on crawled pages

### `match_code_examples(query_embedding, match_count, source_filter)`
Performs vector similarity search on code examples

## Configuration Environment Variables

- `TRANSPORT` - Server transport method (default: "sse")
- `HOST` - Server host (default: "0.0.0.0")
- `PORT` - Server port (default: "8051")
- `SEARXNG_URL` - SearXNG instance URL
- `OPENAI_API_KEY` - OpenAI API key for embeddings
- `SUPABASE_URL` - PostgreSQL connection string
- `SUPABASE_SERVICE_KEY` - Database service key
- `USE_CONTEXTUAL_EMBEDDINGS` - Enable contextual embeddings
- `USE_HYBRID_SEARCH` - Enable hybrid search
- `USE_AGENTIC_RAG` - Enable code example extraction
- `USE_RERANKING` - Enable result reranking
- `USE_KNOWLEDGE_GRAPH` - Enable knowledge graph features
- `NEO4J_URI` - Neo4j connection URI
- `NEO4J_USER` - Neo4j username
- `NEO4J_PASSWORD` - Neo4j password