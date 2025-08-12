"""
MCP server for web crawling with Crawl4AI.

This server provides tools to crawl websites using Crawl4AI, automatically detecting
the appropriate crawl method based on URL type (sitemap, txt file, or regular webpage).
Also includes AI hallucination detection and repository parsing tools using Neo4j knowledge graphs.

Supports both MCP protocol (SSE/stdio) and HTTP REST API endpoints for browser-based clients.
"""
from mcp.server.fastmcp import FastMCP, Context
from sentence_transformers import CrossEncoder
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
from urllib.parse import urlparse, urldefrag
from xml.etree import ElementTree
from dotenv import load_dotenv
from supabase import Client
from pathlib import Path
import requests
import asyncio
import json
import os
import re
import concurrent.futures
import sys
import time
import logging

# Import FastAPI for HTTP API support
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, MemoryAdaptiveDispatcher

# Add knowledge_graphs folder to path for importing knowledge graph modules
knowledge_graphs_path = Path(__file__).resolve().parent.parent / 'knowledge_graphs'
sys.path.append(str(knowledge_graphs_path))

from utils import (
    get_supabase_client, 
    add_documents_to_supabase, 
    search_documents,
    extract_code_blocks,
    generate_code_example_summary,
    add_code_examples_to_supabase,
    update_source_info,
    extract_source_summary,
    search_code_examples
)

# Import HTTP API components
from src.api.responses import APIResponse, HealthResponse, SourcesResponse, SearchResponse, HealthData, SourceData, SearchResultData
from src.api.endpoints import router as api_router

# Initialize FastMCP server first
print("Initializing FastMCP server...")
mcp = FastMCP(
    name="mcp-crawl4ai-rag",
    instructions="MCP server for RAG and web crawling with Crawl4AI"
)

# Get the underlying Starlette app
sse_app = mcp.sse_app()

# Add CORS middleware to the FastMCP app
sse_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware components
from src.api.middleware import RequestLoggingMiddleware, RateLimitMiddleware, SecurityHeadersMiddleware

# Add security headers middleware
sse_app.add_middleware(SecurityHeadersMiddleware)

# Add rate limiting middleware (60 requests per minute)
sse_app.add_middleware(RateLimitMiddleware, calls_per_minute=60)

# Add request logging middleware (add last to capture all request details)
sse_app.add_middleware(RequestLoggingMiddleware)

# Include our custom API router
sse_app.include_router(api_router)

print("✓ FastMCP server initialized with custom endpoints")

# Import knowledge graph modules
from knowledge_graph_validator import KnowledgeGraphValidator
from parse_repo_into_neo4j import DirectNeo4jExtractor
from ai_script_analyzer import AIScriptAnalyzer
from hallucination_reporter import HallucinationReporter

# Load environment variables from the project root .env file
project_root = Path(__file__).resolve().parent.parent
dotenv_path = project_root / '.env'

# Force override of existing environment variables
load_dotenv(dotenv_path, override=True)

# Helper functions for Neo4j validation and error handling
def validate_neo4j_connection() -> bool:
    """Check if Neo4j environment variables are configured."""
    return all([
        os.getenv("NEO4J_URI"),
        os.getenv("NEO4J_USER"),
        os.getenv("NEO4J_PASSWORD")
    ])

def format_neo4j_error(error: Exception) -> str:
    """Format Neo4j connection errors for user-friendly messages."""
    error_str = str(error).lower()
    if "authentication" in error_str or "unauthorized" in error_str:
        return "Neo4j authentication failed. Check NEO4J_USER and NEO4J_PASSWORD."
    elif "connection" in error_str or "refused" in error_str or "timeout" in error_str:
        return "Cannot connect to Neo4j. Check NEO4J_URI and ensure Neo4j is running."
    elif "database" in error_str:
        return "Neo4j database error. Check if the database exists and is accessible."
    else:
        return f"Neo4j error: {str(error)}"

def validate_script_path(script_path: str) -> Dict[str, Any]:
    """Validate script path and return error info if invalid."""
    if not script_path or not isinstance(script_path, str):
        return {"valid": False, "error": "Script path is required"}
    
    if not os.path.exists(script_path):
        return {"valid": False, "error": f"Script not found: {script_path}"}
    
    if not script_path.endswith('.py'):
        return {"valid": False, "error": "Only Python (.py) files are supported"}
    
    try:
        # Check if file is readable
        with open(script_path, 'r', encoding='utf-8') as f:
            f.read(1)  # Read first character to test
        return {"valid": True}
    except Exception as e:
        return {"valid": False, "error": f"Cannot read script file: {str(e)}"}

def validate_github_url(repo_url: str) -> Dict[str, Any]:
    """Validate GitHub repository URL."""
    if not repo_url or not isinstance(repo_url, str):
        return {"valid": False, "error": "Repository URL is required"}
    
    repo_url = repo_url.strip()
    
    # Basic GitHub URL validation
    if not ("github.com" in repo_url.lower() or repo_url.endswith(".git")):
        return {"valid": False, "error": "Please provide a valid GitHub repository URL"}
    
    # Check URL format
    if not (repo_url.startswith("https://") or repo_url.startswith("git@")):
        return {"valid": False, "error": "Repository URL must start with https:// or git@"}
    
    return {"valid": True, "repo_name": repo_url.split('/')[-1].replace('.git', '')}

# Create a dataclass for our application context
@dataclass
class Crawl4AIContext:
    """Context for the Crawl4AI MCP server."""
    crawler: AsyncWebCrawler
    supabase_client: Client
    reranking_model: Optional[CrossEncoder] = None
    knowledge_validator: Optional[Any] = None  # KnowledgeGraphValidator when available
    repo_extractor: Optional[Any] = None       # DirectNeo4jExtractor when available
    initialized: bool = False                  # Track initialization status
    fastapi_app: Optional[FastAPI] = None      # FastAPI app for HTTP endpoints

@asynccontextmanager
async def crawl4ai_lifespan(server: FastMCP) -> AsyncIterator[Crawl4AIContext]:
    """
    Manages the Crawl4AI client lifecycle.
    
    Args:
        server: The FastMCP server instance
        
    Yields:
        Crawl4AIContext: The context containing the Crawl4AI crawler and Supabase client
    """
    print("Starting Crawl4AI MCP server initialization...")
    
    # Create browser configuration
    browser_config = BrowserConfig(
        headless=True,
        verbose=False
    )
    
    # Initialize the crawler
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.__aenter__()
    
    # Initialize Supabase client
    supabase_client = get_supabase_client()
    
    # Initialize cross-encoder model for reranking if enabled
    reranking_model = None
    if os.getenv("USE_RERANKING", "false") == "true":
        try:
            reranking_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        except Exception as e:
            print(f"Failed to load reranking model: {e}")
            reranking_model = None
    
    # Initialize Neo4j components if configured and enabled
    knowledge_validator = None
    repo_extractor = None
    
    # Check if knowledge graph functionality is enabled
    knowledge_graph_enabled = os.getenv("USE_KNOWLEDGE_GRAPH", "false") == "true"
    
    if knowledge_graph_enabled:
        neo4j_uri = os.getenv("NEO4J_URI")
        neo4j_user = os.getenv("NEO4J_USER")
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        
        if neo4j_uri and neo4j_user and neo4j_password:
            try:
                print("Initializing knowledge graph components...")
                
                # Initialize knowledge graph validator
                knowledge_validator = KnowledgeGraphValidator(neo4j_uri, neo4j_user, neo4j_password)
                await knowledge_validator.initialize()
                print("✓ Knowledge graph validator initialized")
                
                # Initialize repository extractor
                repo_extractor = DirectNeo4jExtractor(neo4j_uri, neo4j_user, neo4j_password)
                await repo_extractor.initialize()
                print("✓ Repository extractor initialized")
                
            except Exception as e:
                print(f"Failed to initialize Neo4j components: {format_neo4j_error(e)}")
                knowledge_validator = None
                repo_extractor = None
        else:
            print("Neo4j credentials not configured - knowledge graph tools will be unavailable")
    else:
        print("Knowledge graph functionality disabled - set USE_KNOWLEDGE_GRAPH=true to enable")
    
    # The FastAPI app is already initialized at module level with our custom endpoints
    print("✓ Lifespan initialized - FastAPI app with custom endpoints already configured")
    
    # Create the context with initialization flag
    context = Crawl4AIContext(
        crawler=crawler,
        supabase_client=supabase_client,
        reranking_model=reranking_model,
        knowledge_validator=knowledge_validator,
        repo_extractor=repo_extractor,
        initialized=True,
        fastapi_app=sse_app
    )
    
    print("Crawl4AI MCP server initialization complete!")
    
    try:
        yield context
    finally:
        # Clean up all components
        await crawler.__aexit__(None, None, None)
        if knowledge_validator:
            try:
                await knowledge_validator.close()
                print("✓ Knowledge graph validator closed")
            except Exception as e:
                print(f"Error closing knowledge validator: {e}")
        if repo_extractor:
            try:
                await repo_extractor.close()
                print("✓ Repository extractor closed")
            except Exception as e:
                print(f"Error closing repository extractor: {e}")

# FastMCP server is already initialized above
print("✓ FastMCP server ready with HTTP API endpoints")

def rerank_results(model: CrossEncoder, query: str, results: List[Dict[str, Any]], content_key: str = "content") -> List[Dict[str, Any]]:
    """
    Rerank search results using a cross-encoder model.
    
    Args:
        model: The cross-encoder model to use for reranking
        query: The search query
        results: List of search results
        content_key: The key in each result dict that contains the text content
        
    Returns:
        Reranked list of results
    """
    if not model or not results:
        return results
    
    try:
        # Extract content from results
        texts = [result.get(content_key, "") for result in results]
        
        # Create pairs of [query, document] for the cross-encoder
        pairs = [[query, text] for text in texts]
        
        # Get relevance scores from the cross-encoder
        scores = model.predict(pairs)
        
        # Add scores to results and sort by score (descending)
        for i, result in enumerate(results):
            result["rerank_score"] = float(scores[i])
        
        # Sort by rerank score
        reranked = sorted(results, key=lambda x: x.get("rerank_score", 0), reverse=True)
        
        return reranked
    except Exception as e:
        print(f"Error during reranking: {e}")
        return results

def is_sitemap(url: str) -> bool:
    """
    Check if a URL is a sitemap.
    
    Args:
        url: URL to check
        
    Returns:
        True if the URL is a sitemap, False otherwise
    """
    return url.endswith('sitemap.xml') or 'sitemap' in urlparse(url).path

def is_txt(url: str) -> bool:
    """
    Check if a URL is a text file.
    
    Args:
        url: URL to check
        
    Returns:
        True if the URL is a text file, False otherwise
    """
    return url.endswith('.txt')

def parse_sitemap(sitemap_url: str) -> List[str]:
    """
    Parse a sitemap and extract URLs.
    
    Args:
        sitemap_url: URL of the sitemap
        
    Returns:
        List of URLs found in the sitemap
    """
    resp = requests.get(sitemap_url)
    urls = []

    if resp.status_code == 200:
        try:
            tree = ElementTree.fromstring(resp.content)
            urls = [loc.text for loc in tree.findall('.//{*}loc')]
        except Exception as e:
            print(f"Error parsing sitemap XML: {e}")

    return urls

def smart_chunk_markdown(text: str, chunk_size: int = 5000) -> List[str]:
    """Split text into chunks, respecting code blocks and paragraphs."""
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        # Calculate end position
        end = start + chunk_size

        # If we're at the end of the text, just take what's left
        if end >= text_length:
            chunks.append(text[start:].strip())
            break

        # Try to find a code block boundary first (```)
        chunk = text[start:end]
        code_block = chunk.rfind('```')
        if code_block != -1 and code_block > chunk_size * 0.3:
            end = start + code_block

        # If no code block, try to break at a paragraph
        elif '\n\n' in chunk:
            # Find the last paragraph break
            last_break = chunk.rfind('\n\n')
            if last_break > chunk_size * 0.3:  # Only break if we're past 30% of chunk_size
                end = start + last_break

        # If no paragraph break, try to break at a sentence
        elif '. ' in chunk:
            # Find the last sentence break
            last_period = chunk.rfind('. ')
            if last_period > chunk_size * 0.3:  # Only break if we're past 30% of chunk_size
                end = start + last_period + 1

        # Extract chunk and clean it up
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start position for next chunk
        start = end

    return chunks

def extract_section_info(chunk: str) -> Dict[str, Any]:
    """
    Extracts headers and stats from a chunk.
    
    Args:
        chunk: Markdown chunk
        
    Returns:
        Dictionary with headers and stats
    """
    headers = re.findall(r'^(#+)\s+(.+)$', chunk, re.MULTILINE)
    header_str = '; '.join([f'{h[0]} {h[1]}' for h in headers]) if headers else ''

    return {
        "headers": header_str,
        "char_count": len(chunk),
        "word_count": len(chunk.split())
    }

def process_code_example(args):
    """
    Process a single code example to generate its summary.
    This function is designed to be used with concurrent.futures.
    
    Args:
        args: Tuple containing (code, context_before, context_after)
        
    Returns:
        The generated summary
    """
    code, context_before, context_after = args
    return generate_code_example_summary(code, context_before, context_after)

@mcp.tool()
async def search(ctx: Context, query: str, return_raw_markdown: bool = False, num_results: int = 6, batch_size: int = 20, max_concurrent: int = 10, max_rag_workers: int = 5) -> str:
    """
    Comprehensive search tool that integrates SearXNG search with scraping and RAG functionality.
    Optionally, use `return_raw_markdown=true` to return raw markdown for more detailed analysis.
    
    This tool performs a complete search, scrape, and RAG workflow:
    1. Searches SearXNG with the provided query, obtaining `num_results` URLs
    2. Extracts markdown from URLs, chunks embedding data into Supabase
    3. Scrapes all returned URLs using existing scraping functionality
    4. Returns organized results with comprehensive metadata
    
    Args:
        query: The search query for SearXNG
        return_raw_markdown: If True, skip embedding/RAG and return raw markdown content (default: False)
        num_results: Number of search results to return from SearXNG (default: 6)
        batch_size: Batch size for database operations (default: 20)
        max_concurrent: Maximum concurrent browser sessions for scraping (default: 10)
        max_rag_workers: Maximum concurrent RAG query workers for parallel processing (default: 5)
    
    Returns:
        JSON string with search results, or raw markdown of each URL if `return_raw_markdown=true`
    """
    # Check if server is fully initialized
    if not getattr(ctx.request_context.lifespan_context, 'initialized', False):
        return json.dumps({
            "success": False,
            "error": "Server is still initializing. Please wait a moment and try again."
        }, indent=2)
    
    start_time = time.time()
    
    try:
        # Step 1: Environment validation - check if SEARXNG_URL is configured
        searxng_url = os.getenv("SEARXNG_URL")
        if not searxng_url:
            return json.dumps({
                "success": False,
                "error": "SEARXNG_URL environment variable is not configured. Please set it to your SearXNG instance URL."
            }, indent=2)
        
        searxng_url = searxng_url.rstrip('/')  # Remove trailing slash
        search_endpoint = f"{searxng_url}/search"
        
        # Get optional configuration
        user_agent = os.getenv("SEARXNG_USER_AGENT", "MCP-Crawl4AI-RAG-Server/1.0")
        timeout = int(os.getenv("SEARXNG_TIMEOUT", "30"))
        default_engines = os.getenv("SEARXNG_DEFAULT_ENGINES", "")
        
        # Step 2: SearXNG request - make HTTP GET request with parameters
        headers = {
            "User-Agent": user_agent,
            "Accept": "application/json"
        }
        
        # Prepare request parameters
        params = {
            "q": query,
            "format": "json",
            "categories": "general",
            "limit": num_results  # SearXNG uses 'limit'
        }
        
        # Add engines if specified
        if default_engines:
            params["engines"] = default_engines
        
        print(f"Making SearXNG request to: {search_endpoint}")
        print(f"Parameters: {params}")
        
        # Make the HTTP request to SearXNG
        try:
            response = requests.get(
                search_endpoint,
                params=params,
                headers=headers,
                timeout=timeout
            )
            response.raise_for_status()  # Raise exception for HTTP errors
            
        except requests.exceptions.Timeout:
            return json.dumps({
                "success": False,
                "error": f"SearXNG request timed out after {timeout} seconds. Check your SearXNG instance."
            }, indent=2)
        except requests.exceptions.ConnectionError:
            return json.dumps({
                "success": False,
                "error": f"Cannot connect to SearXNG at {searxng_url}. Check the URL and ensure SearXNG is running."
            }, indent=2)
        except requests.exceptions.HTTPError as e:
            return json.dumps({
                "success": False,
                "error": f"SearXNG HTTP error: {e}. Check your SearXNG configuration."
            }, indent=2)
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"SearXNG request failed: {str(e)}"
            }, indent=2)
        
        # Step 3: Response parsing - extract URLs from SearXNG JSON response
        try:
            search_data = response.json()
        except json.JSONDecodeError as e:
            return json.dumps({
                "success": False,
                "error": f"Invalid JSON response from SearXNG: {str(e)}"
            }, indent=2)
        
        # Extract results from response
        results = search_data.get("results", [])
        if not results:
            return json.dumps({
                "success": False,
                "query": query,
                "error": "No search results returned from SearXNG"
            }, indent=2)
        
        # Step 4: URL filtering - limit to num_results and validate URLs
        valid_urls = []
        for result in results[:num_results]:
            url = result.get("url", "").strip()
            if url and url.startswith(("http://", "https://")):
                valid_urls.append(url)
        
        if not valid_urls:
            return json.dumps({
                "success": False,
                "query": query,
                "error": "No valid URLs found in search results"
            }, indent=2)
        
        print(f"Found {len(valid_urls)} valid URLs to process")
        
        # Step 5: Content processing - use existing scrape_urls function
        try:
            # Use the existing scrape_urls function to scrape all URLs
            scrape_result_str = await scrape_urls(ctx, valid_urls, max_concurrent, batch_size)
            scrape_result = json.loads(scrape_result_str)
            
            if not scrape_result.get("success", False):
                return json.dumps({
                    "success": False,
                    "query": query,
                    "searxng_results": valid_urls,
                    "error": f"Scraping failed: {scrape_result.get('error', 'Unknown error')}"
                }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "query": query,
                "searxng_results": valid_urls,
                "error": f"Scraping error: {str(e)}"
            }, indent=2)
        
        # Step 6: Results processing based on return_raw_markdown flag
        results_data = {}
        processed_urls = 0
        
        if return_raw_markdown:
            # Raw markdown mode - just return scraped content without RAG
            # Get content from database for each URL
            supabase_client = ctx.request_context.lifespan_context.supabase_client
            
            for url in valid_urls:
                try:
                    # Query the database for content from this URL
                    result = supabase_client.from_('crawled_pages')\
                        .select('content')\
                        .eq('url', url)\
                        .execute()
                    
                    if result.data:
                        # Combine all chunks for this URL
                        content_chunks = [row['content'] for row in result.data]
                        combined_content = '\n\n'.join(content_chunks)
                        results_data[url] = combined_content
                        processed_urls += 1
                    else:
                        results_data[url] = "No content found"
                        
                except Exception as e:
                    results_data[url] = f"Error retrieving content: {str(e)}"
        
        else:
            # RAG mode - perform RAG query for each URL with parallel processing
            import asyncio
            
            # Prepare RAG query tasks
            async def process_rag_query_for_url(url: str):
                """Process RAG query for a single URL."""
                url_start_time = time.time()
                print(f"Processing RAG query for URL: {url}")
                
                try:
                    # Extract source_id from URL for RAG filtering
                    parsed_url = urlparse(url)
                    source_id = parsed_url.netloc or parsed_url.path
                    
                    # Validate source_id
                    if not source_id or source_id.strip() == "":
                        print(f"Warning: Empty source_id for URL {url}, using fallback")
                        source_id = "unknown_source"
                    
                    print(f"Using source_id: '{source_id}' for URL: {url}")
                    
                    # Perform RAG query with timeout protection (30 second timeout)
                    try:
                        rag_result_str = await asyncio.wait_for(
                            perform_rag_query(ctx, query, source_id, match_count=5),
                            timeout=30.0
                        )
                        print(f"RAG query completed for {url} in {time.time() - url_start_time:.2f}s")
                    except asyncio.TimeoutError:
                        print(f"RAG query timeout for URL: {url}")
                        return url, "RAG query timed out after 30 seconds"
                    
                    # Parse JSON with error handling
                    try:
                        rag_result = json.loads(rag_result_str)
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error for URL {url}: {e}")
                        return url, f"JSON parsing error: {str(e)}"
                    
                    if rag_result.get("success", False) and rag_result.get("results"):
                        # Format RAG results for this URL
                        formatted_results = []
                        for result in rag_result["results"]:
                            formatted_results.append({
                                "content": result.get("content", ""),
                                "similarity": result.get("similarity", 0),
                                "metadata": result.get("metadata", {})
                            })
                        print(f"Successfully processed RAG results for {url}: {len(formatted_results)} results")
                        return url, formatted_results
                    else:
                        error_msg = rag_result.get("error", "No RAG results found")
                        print(f"No RAG results for {url}: {error_msg}")
                        return url, f"No relevant results: {error_msg}"
                        
                except Exception as e:
                    print(f"Unexpected error processing URL {url}: {str(e)}")
                    return url, f"RAG query error: {str(e)}"
            
            # Use provided max_rag_workers or get from environment or use default
            if max_rag_workers is None:
                max_rag_workers = int(os.getenv("MAX_RAG_WORKERS", "5"))
            
            # Create tasks for parallel execution with semaphore for rate limiting
            semaphore = asyncio.Semaphore(max_rag_workers)
            
            async def rate_limited_rag_query(url):
                async with semaphore:
                    return await process_rag_query_for_url(url)
            
            # Execute all RAG queries in parallel
            rag_tasks = [rate_limited_rag_query(url) for url in valid_urls]
            rag_results = await asyncio.gather(*rag_tasks)
            
            # Process results
            for url, result in rag_results:
                results_data[url] = result
                if isinstance(result, list):  # Successfully got results
                    processed_urls += 1
        
        # Calculate processing statistics
        processing_time = time.time() - start_time
        
        # Step 7: Format final results according to specification
        return json.dumps({
            "success": True,
            "query": query,
            "searxng_results": valid_urls,
            "mode": "raw_markdown" if return_raw_markdown else "rag_query",
            "results": results_data,
            "summary": {
                "urls_found": len(results),
                "urls_scraped": len(valid_urls),
                "urls_processed": processed_urls,
                "processing_time_seconds": round(processing_time, 2)
            },
            "performance": {
                "num_results": num_results,
                "batch_size": batch_size,
                "max_concurrent": max_concurrent,
                "max_rag_workers": max_rag_workers,
                "searxng_endpoint": search_endpoint
            }
        }, indent=2)
        
    except Exception as e:
        processing_time = time.time() - start_time
        return json.dumps({
            "success": False,
            "query": query,
            "error": f"Search operation failed: {str(e)}",
            "processing_time_seconds": round(processing_time, 2)
        }, indent=2)

@mcp.tool()
async def scrape_urls(ctx: Context, url: Union[str, List[str]], max_concurrent: int = 10, batch_size: int = 20, return_raw_markdown: bool = False) -> str:
    """
    Scrape **one or more URLs** and store their contents as embedding chunks in Supabase.
    Optionally, use `return_raw_markdown=true` to return raw markdown content without storing.
    
    The content is scraped and stored in Supabase for later retrieval and querying via perform_rag_query tool, unless
    `return_raw_markdown=True` is specified, in which case raw markdown is returned directly.
    
    Args:
        url: URL to scrape, or list of URLs for batch processing
        max_concurrent: Maximum number of concurrent browser sessions for multi-URL mode (default: 10)
        batch_size: Size of batches for database operations (default: 20)
        return_raw_markdown: If True, skip database storage and return raw markdown content (default: False)
    
    Returns:
        Summary of the scraping operation and storage in Supabase, or raw markdown content if requested
    """
    # Check if server is fully initialized
    if not getattr(ctx.request_context.lifespan_context, 'initialized', False):
        return json.dumps({
            "success": False,
            "error": "Server is still initializing. Please wait a moment and try again."
        }, indent=2)
    
    start_time = time.time()
    
    try:
        # Input validation and type detection
        if isinstance(url, str):
            # Single URL - convert to list for unified processing
            urls_to_process = [url]
        elif isinstance(url, list):
            # Multiple URLs
            if not url:
                return json.dumps({
                    "success": False,
                    "error": "URL list cannot be empty"
                }, indent=2)
            
            # Validate all URLs are strings and remove duplicates
            validated_urls = []
            for i, u in enumerate(url):
                if not isinstance(u, str):
                    return json.dumps({
                        "success": False,
                        "error": f"URL at index {i} must be a string, got {type(u).__name__}"
                    }, indent=2)
                if u.strip():  # Only add non-empty URLs
                    validated_urls.append(u.strip())
            
            if not validated_urls:
                return json.dumps({
                    "success": False,
                    "error": "No valid URLs found in the list"
                }, indent=2)
            
            # Remove duplicates while preserving order
            seen = set()
            urls_to_process = []
            for u in validated_urls:
                if u not in seen:
                    seen.add(u)
                    urls_to_process.append(u)
        else:
            return json.dumps({
                "success": False,
                "error": f"URL must be a string or list of strings, got {type(url).__name__}"
            }, indent=2)
        
        # Get context components
        crawler = ctx.request_context.lifespan_context.crawler
        supabase_client = ctx.request_context.lifespan_context.supabase_client
        
        # Always use unified processing (handles both single and multiple URLs seamlessly)
        return await _process_multiple_urls(
            crawler, supabase_client, urls_to_process,
            max_concurrent, batch_size, start_time, return_raw_markdown
        )
            
    except Exception as e:
        processing_time = time.time() - start_time
        return json.dumps({
            "success": False,
            "url": url if isinstance(url, str) else f"[{len(url)} URLs]" if isinstance(url, list) else str(url),
            "error": str(e),
            "processing_time_seconds": round(processing_time, 2)
        }, indent=2)


async def _process_multiple_urls(
    crawler: AsyncWebCrawler,
    supabase_client: Client,
    urls: List[str],
    max_concurrent: int,
    batch_size: int,
    start_time: float,
    return_raw_markdown: bool = False
) -> str:
    """
    Process one or more URLs using batch crawling and enhanced error handling.
    
    This function seamlessly handles both single URL and multiple URL scenarios,
    maintaining backward compatibility for single URL inputs while providing
    enhanced performance and error handling for all cases.
    
    Args:
        crawler: AsyncWebCrawler instance
        supabase_client: Supabase client
        urls: List of URLs to process (can be single URL or multiple)
        max_concurrent: Maximum concurrent browser sessions
        batch_size: Batch size for database operations
        start_time: Start time for performance tracking
        
    Returns:
        JSON string with crawl results (single URL format for 1 URL, multi format for multiple)
    """
    try:
        # Batch crawl all URLs using existing infrastructure
        crawl_results = await crawl_batch(crawler, urls, max_concurrent=max_concurrent)
        
        # Raw markdown mode - return immediately without storing
        if return_raw_markdown:
            results = {}
            total_content_length = 0
            urls_processed = 0
            
            for original_url in urls:
                # Find matching result
                crawl_result = None
                for cr in crawl_results:
                    if cr['url'] == original_url:
                        crawl_result = cr
                        break
                
                if crawl_result and crawl_result.get('markdown'):
                    results[original_url] = crawl_result['markdown']
                    total_content_length += len(crawl_result['markdown'])
                    urls_processed += 1
                else:
                    results[original_url] = "No content retrieved"
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            return json.dumps({
                "success": True,
                "mode": "raw_markdown",
                "results": results,
                "summary": {
                    "urls_processed": urls_processed,
                    "total_content_length": total_content_length,
                    "processing_time_seconds": round(processing_time, 2)
                }
            }, indent=2)
        
        # Initialize tracking variables for normal (database storage) mode
        all_urls = []
        all_chunk_numbers = []
        all_contents = []
        all_metadatas = []
        all_url_to_full_document = {}
        
        # Track sources and processing results
        source_content_map = {}
        source_word_counts = {}
        
        # Track individual URL results for detailed reporting
        url_results = []
        successful_urls = 0
        failed_urls = 0
        total_chunks = 0
        total_content_length = 0
        total_word_count = 0
        errors = []
        
        # Process each crawl result
        for original_url in urls:
            # Find matching result
            crawl_result = None
            for cr in crawl_results:
                if cr['url'] == original_url:
                    crawl_result = cr
                    break
            
            if crawl_result and crawl_result.get('markdown'):
                # Successful crawl
                try:
                    # Extract source_id
                    parsed_url = urlparse(original_url)
                    source_id = parsed_url.netloc or parsed_url.path
                    
                    # Chunk the content
                    chunks = smart_chunk_markdown(crawl_result['markdown'])
                    
                    # Store content for source summary generation
                    if source_id not in source_content_map:
                        source_content_map[source_id] = crawl_result['markdown'][:5000]
                        source_word_counts[source_id] = 0
                    
                    url_word_count = 0
                    
                    # Process chunks
                    for i, chunk in enumerate(chunks):
                        all_urls.append(original_url)
                        all_chunk_numbers.append(i)
                        all_contents.append(chunk)
                        
                        # Extract metadata
                        meta = extract_section_info(chunk)
                        meta["chunk_index"] = i
                        meta["url"] = original_url
                        meta["source"] = source_id
                        meta["crawl_type"] = "multi_url"
                        meta["crawl_time"] = str(asyncio.current_task().get_coro().__name__)
                        all_metadatas.append(meta)
                        
                        # Accumulate word counts
                        chunk_word_count = meta.get("word_count", 0)
                        url_word_count += chunk_word_count
                        source_word_counts[source_id] += chunk_word_count
                        total_word_count += chunk_word_count
                    
                    # Store full document mapping
                    all_url_to_full_document[original_url] = crawl_result['markdown']
                    
                    # Track successful URL result
                    url_results.append({
                        "url": original_url,
                        "success": True,
                        "chunks_stored": len(chunks),
                        "content_length": len(crawl_result['markdown']),
                        "word_count": url_word_count,
                        "source_id": source_id
                    })
                    
                    successful_urls += 1
                    total_chunks += len(chunks)
                    total_content_length += len(crawl_result['markdown'])
                    
                except Exception as e:
                    # Error processing successful crawl
                    error_detail = {
                        "url": original_url,
                        "error": str(e),
                        "phase": "processing"
                    }
                    errors.append(error_detail)
                    url_results.append({
                        "url": original_url,
                        "success": False,
                        "error": str(e)
                    })
                    failed_urls += 1
            else:
                # Failed crawl
                error_msg = "No content retrieved"
                error_detail = {
                    "url": original_url,
                    "error": error_msg,
                    "phase": "crawl"
                }
                errors.append(error_detail)
                url_results.append({
                    "url": original_url,
                    "success": False,
                    "error": error_msg
                })
                failed_urls += 1
        
        # Update source information in parallel (if any successful crawls)
        if source_content_map:
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                source_summary_args = [(source_id, content) for source_id, content in source_content_map.items()]
                source_summaries = list(executor.map(lambda args: extract_source_summary(args[0], args[1]), source_summary_args))
            
            for (source_id, _), summary in zip(source_summary_args, source_summaries):
                word_count = source_word_counts.get(source_id, 0)
                update_source_info(supabase_client, source_id, summary, word_count)
        
        # Add documentation chunks to Supabase in batches (if any)
        if all_contents:
            add_documents_to_supabase(
                supabase_client,
                all_urls,
                all_chunk_numbers,
                all_contents,
                all_metadatas,
                all_url_to_full_document,
                batch_size=batch_size
            )
        
        # Process code examples from all successful documents (if enabled)
        total_code_examples = 0
        extract_code_examples_enabled = os.getenv("USE_AGENTIC_RAG", "false") == "true"
        if extract_code_examples_enabled and crawl_results:
            code_urls = []
            code_chunk_numbers = []
            code_examples = []
            code_summaries = []
            code_metadatas = []
            
            # Extract code blocks from all successful documents
            for doc in crawl_results:
                if doc.get('markdown'):
                    source_url = doc['url']
                    md = doc['markdown']
                    code_blocks = extract_code_blocks(md)
                    
                    if code_blocks:
                        # Process code examples in parallel
                        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                            summary_args = [(block['code'], block['context_before'], block['context_after'])
                                            for block in code_blocks]
                            summaries = list(executor.map(process_code_example, summary_args))
                        
                        # Prepare code example data
                        parsed_url = urlparse(source_url)
                        source_id = parsed_url.netloc or parsed_url.path
                        
                        for i, (block, summary) in enumerate(zip(code_blocks, summaries)):
                            code_urls.append(source_url)
                            code_chunk_numbers.append(len(code_examples))
                            code_examples.append(block['code'])
                            code_summaries.append(summary)
                            
                            code_meta = {
                                "chunk_index": len(code_examples) - 1,
                                "url": source_url,
                                "source": source_id,
                                "char_count": len(block['code']),
                                "word_count": len(block['code'].split())
                            }
                            code_metadatas.append(code_meta)
            
            # Add all code examples to Supabase
            if code_examples:
                add_code_examples_to_supabase(
                    supabase_client,
                    code_urls,
                    code_chunk_numbers,
                    code_examples,
                    code_summaries,
                    code_metadatas,
                    batch_size=batch_size
                )
                total_code_examples = len(code_examples)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Return format based on number of URLs (maintain backward compatibility)
        if len(urls) == 1:
            # Single URL mode - return legacy-compatible format
            single_url_result = url_results[0] if url_results else None
            if single_url_result and single_url_result["success"]:
                # Get the first crawl result for links information
                first_crawl_result = None
                for cr in crawl_results:
                    if cr['url'] == urls[0]:
                        first_crawl_result = cr
                        break
                
                return json.dumps({
                    "success": True,
                    "url": urls[0],
                    "chunks_stored": single_url_result.get("chunks_stored", 0),
                    "code_examples_stored": total_code_examples,
                    "content_length": single_url_result.get("content_length", 0),
                    "total_word_count": single_url_result.get("word_count", 0),
                    "source_id": single_url_result.get("source_id", ""),
                    "links_count": {
                        "internal": len(first_crawl_result.get("links", {}).get("internal", [])) if first_crawl_result else 0,
                        "external": len(first_crawl_result.get("links", {}).get("external", [])) if first_crawl_result else 0
                    }
                }, indent=2)
            else:
                # Single URL failed
                error_msg = single_url_result.get("error", "No content retrieved") if single_url_result else "No content retrieved"
                return json.dumps({
                    "success": False,
                    "url": urls[0],
                    "error": error_msg
                }, indent=2)
        else:
            # Multiple URLs mode - return comprehensive results
            return json.dumps({
                "success": True,
                "mode": "multi_url",
                "summary": {
                    "total_urls": len(urls),
                    "successful_urls": successful_urls,
                    "failed_urls": failed_urls,
                    "total_chunks_stored": total_chunks,
                    "total_code_examples_stored": total_code_examples,
                    "total_content_length": total_content_length,
                    "total_word_count": total_word_count,
                    "sources_updated": len(source_content_map),
                    "processing_time_seconds": round(processing_time, 2)
                },
                "results": url_results,
                "errors": errors if errors else [],
                "performance": {
                    "max_concurrent": max_concurrent,
                    "batch_size": batch_size,
                    "average_time_per_url": round(processing_time / len(urls), 2) if urls else 0
                }
            }, indent=2)
        
    except Exception as e:
        processing_time = time.time() - start_time
        if len(urls) == 1:
            # Single URL error - return legacy-compatible format
            return json.dumps({
                "success": False,
                "url": urls[0],
                "error": str(e)
            }, indent=2)
        else:
            # Multiple URLs error
            return json.dumps({
                "success": False,
                "mode": "multi_url",
                "error": str(e),
                "summary": {
                    "total_urls": len(urls),
                    "processing_time_seconds": round(processing_time, 2)
                }
            }, indent=2)

@mcp.tool()
async def smart_crawl_url(ctx: Context, url: str, max_depth: int = 3, max_concurrent: int = 10, chunk_size: int = 5000, return_raw_markdown: bool = False, query: List[str] = None, max_rag_workers: int = 5) -> str:
    """
    Intelligently crawl a URL based on its type and store content in Supabase.
    Enhanced with raw markdown return and RAG query capabilities.
    
    This tool automatically detects the URL type and applies the appropriate crawling method:
    - For sitemaps: Extracts and crawls all URLs in parallel
    - For text files (llms.txt): Directly retrieves the content
    - For regular webpages: Recursively crawls internal links up to the specified depth
    
    All crawled content is chunked and stored in Supabase for later retrieval and querying.
    
    Args:
        url: URL to crawl (can be a regular webpage, sitemap.xml, or .txt file)
        max_depth: Maximum recursion depth for regular URLs (default: 3)
        max_concurrent: Maximum number of concurrent browser sessions (default: 10)
        chunk_size: Maximum size of each content chunk in characters (default: 5000)
        return_raw_markdown: If True, return raw markdown content instead of just storing (default: False)
        query: List of queries to perform RAG search on crawled content (default: None)
        max_rag_workers: Maximum concurrent RAG query workers for parallel processing (default: 5)
    
    Returns:
        JSON string with crawl summary, raw markdown (if requested), or RAG query results
    """
    # Check if server is fully initialized
    if not getattr(ctx.request_context.lifespan_context, 'initialized', False):
        return json.dumps({
            "success": False,
            "error": "Server is still initializing. Please wait a moment and try again."
        }, indent=2)
    
    try:
        # Get the crawler from the context
        crawler = ctx.request_context.lifespan_context.crawler
        supabase_client = ctx.request_context.lifespan_context.supabase_client
        
        # Determine the crawl strategy
        crawl_results = []
        crawl_type = None
        
        if is_txt(url):
            # For text files, use simple crawl
            crawl_results = await crawl_markdown_file(crawler, url)
            crawl_type = "text_file"
        elif is_sitemap(url):
            # For sitemaps, extract URLs and crawl in parallel
            sitemap_urls = parse_sitemap(url)
            if not sitemap_urls:
                return json.dumps({
                    "success": False,
                    "url": url,
                    "error": "No URLs found in sitemap"
                }, indent=2)
            crawl_results = await crawl_batch(crawler, sitemap_urls, max_concurrent=max_concurrent)
            crawl_type = "sitemap"
        else:
            # For regular URLs, use recursive crawl
            crawl_results = await crawl_recursive_internal_links(crawler, [url], max_depth=max_depth, max_concurrent=max_concurrent)
            crawl_type = "webpage"
        
        if not crawl_results:
            return json.dumps({
                "success": False,
                "url": url,
                "error": "No content found"
            }, indent=2)
        
        # Raw markdown mode - return immediately without storing
        if return_raw_markdown:
            results = {}
            total_content_length = 0
            
            for doc in crawl_results:
                results[doc['url']] = doc['markdown']
                total_content_length += len(doc['markdown'])
            
            return json.dumps({
                "success": True,
                "mode": "raw_markdown",
                "crawl_type": crawl_type,
                "results": results,
                "summary": {
                    "pages_crawled": len(crawl_results),
                    "total_content_length": total_content_length
                }
            }, indent=2)
        
        # Process results and store in Supabase for default and query modes
        urls = []
        chunk_numbers = []
        contents = []
        metadatas = []
        chunk_count = 0
        
        # Track sources and their content
        source_content_map = {}
        source_word_counts = {}
        
        # Process documentation chunks
        for doc in crawl_results:
            source_url = doc['url']
            md = doc['markdown']
            chunks = smart_chunk_markdown(md, chunk_size=chunk_size)
            
            # Extract source_id
            parsed_url = urlparse(source_url)
            source_id = parsed_url.netloc or parsed_url.path
            
            # Store content for source summary generation
            if source_id not in source_content_map:
                source_content_map[source_id] = md[:5000]  # Store first 5000 chars
                source_word_counts[source_id] = 0
            
            for i, chunk in enumerate(chunks):
                urls.append(source_url)
                chunk_numbers.append(i)
                contents.append(chunk)
                
                # Extract metadata
                meta = extract_section_info(chunk)
                meta["chunk_index"] = i
                meta["url"] = source_url
                meta["source"] = source_id
                meta["crawl_type"] = crawl_type
                meta["crawl_time"] = str(asyncio.current_task().get_coro().__name__)
                metadatas.append(meta)
                
                # Accumulate word count
                source_word_counts[source_id] += meta.get("word_count", 0)
                
                chunk_count += 1
        
        # Create url_to_full_document mapping
        url_to_full_document = {}
        for doc in crawl_results:
            url_to_full_document[doc['url']] = doc['markdown']
        
        # Update source information for each unique source FIRST (before inserting documents)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            source_summary_args = [(source_id, content) for source_id, content in source_content_map.items()]
            source_summaries = list(executor.map(lambda args: extract_source_summary(args[0], args[1]), source_summary_args))
        
        for (source_id, _), summary in zip(source_summary_args, source_summaries):
            word_count = source_word_counts.get(source_id, 0)
            update_source_info(supabase_client, source_id, summary, word_count)
        
        # Add documentation chunks to Supabase (AFTER sources exist)
        batch_size = 20
        add_documents_to_supabase(supabase_client, urls, chunk_numbers, contents, metadatas, url_to_full_document, batch_size=batch_size)
        
        # Extract and process code examples from all documents only if enabled
        code_examples = []
        extract_code_examples_enabled = os.getenv("USE_AGENTIC_RAG", "false") == "true"
        if extract_code_examples_enabled:
            all_code_blocks = []
            code_urls = []
            code_chunk_numbers = []
            code_summaries = []
            code_metadatas = []
            
            # Extract code blocks from all documents
            for doc in crawl_results:
                source_url = doc['url']
                md = doc['markdown']
                code_blocks = extract_code_blocks(md)
                
                if code_blocks:
                    # Process code examples in parallel
                    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                        # Prepare arguments for parallel processing
                        summary_args = [(block['code'], block['context_before'], block['context_after'])
                                        for block in code_blocks]
                        
                        # Generate summaries in parallel
                        summaries = list(executor.map(process_code_example, summary_args))
                    
                    # Prepare code example data
                    parsed_url = urlparse(source_url)
                    source_id = parsed_url.netloc or parsed_url.path
                    
                    for i, (block, summary) in enumerate(zip(code_blocks, summaries)):
                        code_urls.append(source_url)
                        code_chunk_numbers.append(len(code_examples))  # Use global code example index
                        code_examples.append(block['code'])
                        code_summaries.append(summary)
                        
                        # Create metadata for code example
                        code_meta = {
                            "chunk_index": len(code_examples) - 1,
                            "url": source_url,
                            "source": source_id,
                            "char_count": len(block['code']),
                            "word_count": len(block['code'].split())
                        }
                        code_metadatas.append(code_meta)
            
            # Add all code examples to Supabase
            if code_examples:
                add_code_examples_to_supabase(
                    supabase_client,
                    code_urls,
                    code_chunk_numbers,
                    code_examples,
                    code_summaries,
                    code_metadatas,
                    batch_size=batch_size
                )
        
        # Query mode - perform RAG queries on all crawled URLs with parallel processing
        if query and len(query) > 0:
            results = {}
            total_rag_queries = 0
            
            # Prepare all RAG query tasks for parallel execution
            async def process_single_rag_query(doc_url: str, q: str, source_id: str):
                """Process a single RAG query for a URL and query combination."""
                try:
                    # Perform RAG query using existing function
                    rag_result_str = await perform_rag_query(ctx, q, source_id, match_count=5)
                    rag_result = json.loads(rag_result_str)
                    
                    if rag_result.get("success", False) and rag_result.get("results"):
                        # Format RAG results for this URL and query
                        formatted_results = []
                        for result in rag_result["results"]:
                            formatted_results.append({
                                "content": result.get("content", ""),
                                "similarity": result.get("similarity", 0),
                                "metadata": result.get("metadata", {})
                            })
                        return doc_url, q, formatted_results
                    else:
                        return doc_url, q, "No relevant results found"
                    
                except Exception as e:
                    return doc_url, q, f"RAG query error: {str(e)}"
            
            # Use provided max_rag_workers or get from environment or use default
            if max_rag_workers is None:
                max_rag_workers = int(os.getenv("MAX_RAG_WORKERS", "5"))
            
            # Create semaphore for rate limiting
            semaphore = asyncio.Semaphore(max_rag_workers)
            
            async def rate_limited_query(doc_url, q, source_id):
                async with semaphore:
                    return await process_single_rag_query(doc_url, q, source_id)
            
            # Build list of all query tasks
            query_tasks = []
            for doc in crawl_results:
                doc_url = doc['url']
                # Extract source_id from URL for RAG filtering
                parsed_url = urlparse(doc_url)
                source_id = parsed_url.netloc or parsed_url.path
                
                results[doc_url] = {}
                
                for q in query:
                    query_tasks.append(rate_limited_query(doc_url, q, source_id))
            
            # Execute all queries in parallel
            query_results = await asyncio.gather(*query_tasks)
            
            # Process results
            for doc_url, q, result in query_results:
                results[doc_url][q] = result
                total_rag_queries += 1
            
            return json.dumps({
                "success": True,
                "mode": "rag_query",
                "crawl_type": crawl_type,
                "results": results,
                "summary": {
                    "pages_crawled": len(crawl_results),
                    "queries_processed": len(query),
                    "total_rag_queries": total_rag_queries,
                    "max_rag_workers": max_rag_workers
                }
            }, indent=2)
        
        # Default mode - return crawl statistics as before
        return json.dumps({
            "success": True,
            "url": url,
            "crawl_type": crawl_type,
            "pages_crawled": len(crawl_results),
            "chunks_stored": chunk_count,
            "code_examples_stored": len(code_examples),
            "sources_updated": len(source_content_map),
            "urls_crawled": [doc['url'] for doc in crawl_results][:5] + (["..."] if len(crawl_results) > 5 else [])
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "url": url,
            "error": str(e)
        }, indent=2)

@mcp.tool()
async def get_available_sources(ctx: Context) -> str:
    """
    Get all available sources from the sources table.
    
    This tool returns a list of all unique sources (domains) that have been crawled and stored
    in the database, along with their summaries and statistics. This is useful for discovering 
    what content is available for querying.

    Always use this tool before calling the RAG query or code example query tool
    with a specific source filter!
    
    Args:
        NONE
    
    Returns:
        JSON string with the list of available sources and their details
    """
    # Check if server is fully initialized
    if not getattr(ctx.request_context.lifespan_context, 'initialized', False):
        return json.dumps({
            "success": False,
            "error": "Server is still initializing. Please wait a moment and try again."
        }, indent=2)
    
    try:
        # Get the Supabase client from the context
        supabase_client = ctx.request_context.lifespan_context.supabase_client
        
        # Query the sources table directly
        result = supabase_client.from_('sources')\
            .select('*')\
            .order('source_id')\
            .execute()
        
        # Format the sources with their details
        sources = []
        if result.data:
            for source in result.data:
                sources.append({
                    "source_id": source.get("source_id"),
                    "summary": source.get("summary"),
                    "total_words": source.get("total_words"),
                    "created_at": source.get("created_at"),
                    "updated_at": source.get("updated_at")
                })
        
        return json.dumps({
            "success": True,
            "sources": sources,
            "count": len(sources)
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)

@mcp.tool()
async def perform_rag_query(ctx: Context, query: str, source: str = None, match_count: int = 5) -> str:
    """
    Perform a RAG (Retrieval Augmented Generation) query on the stored content.
    
    This tool searches the vector database for content relevant to the query and returns
    the matching documents. Optionally filter by source domain.
    Get the source by using the get_available_sources tool before calling this search!
    
    Args:
        query: The search query
        source: Optional source domain to filter results (e.g., 'example.com')
        match_count: Maximum number of results to return (default: 5)
    
    Returns:
        JSON string with the search results
    """
    # Check if server is fully initialized
    if not getattr(ctx.request_context.lifespan_context, 'initialized', False):
        return json.dumps({
            "success": False,
            "error": "Server is still initializing. Please wait a moment and try again."
        }, indent=2)
    
    import asyncio
    
    query_start_time = time.time()
    
    try:
        print(f"Starting RAG query: '{query}' with source filter: '{source}'")
        
        # Input validation
        if not query or not query.strip():
            return json.dumps({
                "success": False,
                "error": "Query cannot be empty"
            }, indent=2)
        
        if match_count <= 0:
            match_count = 5
        elif match_count > 50:  # Reasonable limit
            match_count = 50
        
        # Validate and sanitize source filter
        if source:
            source = source.strip()
            if not source:
                source = None
            elif len(source) > 200:  # Reasonable limit
                return json.dumps({
                    "success": False,
                    "error": "Source filter too long (max 200 characters)"
                }, indent=2)
        
        # Get the Supabase client from the context
        supabase_client = ctx.request_context.lifespan_context.supabase_client
        
        if not supabase_client:
            return json.dumps({
                "success": False,
                "error": "Database client not available"
            }, indent=2)
        
        # Check if hybrid search is enabled
        use_hybrid_search = os.getenv("USE_HYBRID_SEARCH", "false") == "true"
        
        # Prepare source filter if source is provided and not empty
        # The source parameter should be the source_id (domain) not full URL
        if source:
            print(f"[DEBUG] Using source filter: '{source}'")
        
        results = []
        
        if use_hybrid_search:
            print("[DEBUG] Using hybrid search mode")
            try:
                # Hybrid search: combine vector and keyword search with timeout protection
                
                # 1. Get vector search results with timeout (15 seconds)
                print("[DEBUG] Executing vector search...")
                try:
                    vector_results = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None,
                            lambda: search_documents(
                                client=supabase_client,
                                query=query,
                                match_count=match_count * 2,  # Get double to have room for filtering
                                source_id_filter=source  # Use source_id_filter instead of filter_metadata
                            )
                        ),
                        timeout=15.0
                    )
                    print(f"Vector search completed: {len(vector_results)} results")
                except asyncio.TimeoutError:
                    print("Vector search timed out, falling back to keyword search only")
                    vector_results = []
                except Exception as e:
                    print(f"Vector search failed: {e}, falling back to keyword search only")
                    vector_results = []
                
                # 2. Get keyword search results with timeout (10 seconds)
                print("Executing keyword search...")
                try:
                    keyword_query = supabase_client.from_('crawled_pages')\
                        .select('id, url, chunk_number, content, metadata, source_id')\
                        .ilike('content', f'%{query}%')
                    
                    # Apply source filter if provided
                    if source:
                        keyword_query = keyword_query.eq('source_id', source)
                    
                    # Execute keyword search with timeout
                    keyword_response = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None,
                            lambda: keyword_query.limit(match_count * 2).execute()
                        ),
                        timeout=10.0
                    )
                    keyword_results = keyword_response.data if keyword_response.data else []
                    print(f"Keyword search completed: {len(keyword_results)} results")
                except asyncio.TimeoutError:
                    print("Keyword search timed out")
                    keyword_results = []
                except Exception as e:
                    print(f"Keyword search failed: {e}")
                    keyword_results = []
                
                # 3. Combine results with preference for items appearing in both
                if vector_results or keyword_results:
                    seen_ids = set()
                    combined_results = []
                    
                    # First, add items that appear in both searches (these are the best matches)
                    vector_ids = {r.get('id') for r in vector_results if r.get('id')}
                    for kr in keyword_results:
                        if kr['id'] in vector_ids and kr['id'] not in seen_ids:
                            # Find the vector result to get similarity score
                            for vr in vector_results:
                                if vr.get('id') == kr['id']:
                                    # Boost similarity score for items in both results
                                    vr['similarity'] = min(1.0, vr.get('similarity', 0) * 1.2)
                                    combined_results.append(vr)
                                    seen_ids.add(kr['id'])
                                    break
                    
                    # Then add remaining vector results (semantic matches without exact keyword)
                    for vr in vector_results:
                        if vr.get('id') and vr['id'] not in seen_ids and len(combined_results) < match_count:
                            combined_results.append(vr)
                            seen_ids.add(vr['id'])
                    
                    # Finally, add pure keyword matches if we still need more results
                    for kr in keyword_results:
                        if kr['id'] not in seen_ids and len(combined_results) < match_count:
                            # Convert keyword result to match vector result format
                            combined_results.append({
                                'id': kr['id'],
                                'url': kr['url'],
                                'chunk_number': kr['chunk_number'],
                                'content': kr['content'],
                                'metadata': kr['metadata'],
                                'source_id': kr['source_id'],
                                'similarity': 0.5  # Default similarity for keyword-only matches
                            })
                            seen_ids.add(kr['id'])
                    
                    # Use combined results
                    results = combined_results[:match_count]
                    print(f"Hybrid search combined: {len(results)} final results")
                else:
                    print("No results from either vector or keyword search")
                    results = []
                    
            except Exception as e:
                print(f"Hybrid search failed: {e}, falling back to vector search")
                use_hybrid_search = False
        
        if not use_hybrid_search:
            print("[DEBUG] Using vector search only")
            try:
                # Standard vector search with timeout protection (20 seconds)
                results = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: search_documents(
                            client=supabase_client,
                            query=query,
                            match_count=match_count,
                            source_id_filter=source  # Use source_id_filter instead of filter_metadata
                        )
                    ),
                    timeout=20.0
                )
                print(f"Vector search completed: {len(results)} results")
            except asyncio.TimeoutError:
                print("Vector search timed out")
                return json.dumps({
                    "success": False,
                    "query": query,
                    "error": "Search query timed out after 20 seconds. Try reducing match_count or simplifying the query."
                }, indent=2)
            except Exception as e:
                print(f"Vector search failed: {e}")
                return json.dumps({
                    "success": False,
                    "query": query,
                    "error": f"Database search failed: {str(e)}"
                }, indent=2)
        
        # Apply reranking if enabled and we have results
        use_reranking = os.getenv("USE_RERANKING", "false") == "true"
        if use_reranking and results and ctx.request_context.lifespan_context.reranking_model:
            try:
                print("Applying reranking...")
                reranked_results = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: rerank_results(
                            ctx.request_context.lifespan_context.reranking_model,
                            query,
                            results,
                            content_key="content"
                        )
                    ),
                    timeout=10.0
                )
                results = reranked_results
                print("Reranking completed")
            except asyncio.TimeoutError:
                print("Reranking timed out, using original results")
            except Exception as e:
                print(f"Reranking failed: {e}, using original results")
        
        # Format the results
        formatted_results = []
        for result in results:
            try:
                formatted_result = {
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "metadata": result.get("metadata", {}),
                    "similarity": result.get("similarity", 0.0)
                }
                # Include rerank score if available
                if "rerank_score" in result:
                    formatted_result["rerank_score"] = result["rerank_score"]
                formatted_results.append(formatted_result)
            except Exception as e:
                print(f"Error formatting result: {e}")
                continue
        
        processing_time = time.time() - query_start_time
        print(f"RAG query completed in {processing_time:.2f}s with {len(formatted_results)} results")
        
        return json.dumps({
            "success": True,
            "query": query,
            "source_filter": source,
            "search_mode": "hybrid" if use_hybrid_search else "vector",
            "reranking_applied": use_reranking and ctx.request_context.lifespan_context.reranking_model is not None,
            "results": formatted_results,
            "count": len(formatted_results),
            "processing_time_seconds": round(processing_time, 2)
        }, indent=2)
        
    except Exception as e:
        processing_time = time.time() - query_start_time
        print(f"RAG query failed after {processing_time:.2f}s: {e}")
        return json.dumps({
            "success": False,
            "query": query,
            "source_filter": source,
            "error": f"Search operation failed: {str(e)}",
            "processing_time_seconds": round(processing_time, 2)
        }, indent=2)

@mcp.tool()
async def search_code_examples(ctx: Context, query: str, source_id: str = None, match_count: int = 5) -> str:
    """
    Search for code examples relevant to the query.
    
    This tool searches the vector database for code examples relevant to the query and returns
    the matching examples with their summaries. Optionally filter by source_id.
    Get the source_id by using the get_available_sources tool before calling this search!

    Use the get_available_sources tool first to see what sources are available for filtering.
    
    Args:
        query: The search query
        source_id: Optional source ID to filter results (e.g., 'example.com')
        match_count: Maximum number of results to return (default: 5)
    
    Returns:
        JSON string with the search results
    """
    # Check if server is fully initialized
    if not getattr(ctx.request_context.lifespan_context, 'initialized', False):
        return json.dumps({
            "success": False,
            "error": "Server is still initializing. Please wait a moment and try again."
        }, indent=2)
    
    # Check if code example extraction is enabled
    extract_code_examples_enabled = os.getenv("USE_AGENTIC_RAG", "false") == "true"
    if not extract_code_examples_enabled:
        return json.dumps({
            "success": False,
            "error": "Code example extraction is disabled. Perform a normal RAG search."
        }, indent=2)
    
    try:
        # Get the Supabase client from the context
        supabase_client = ctx.request_context.lifespan_context.supabase_client
        
        # Check if hybrid search is enabled
        use_hybrid_search = os.getenv("USE_HYBRID_SEARCH", "false") == "true"
        
        # Prepare filter if source is provided and not empty
        filter_metadata = None
        if source_id and source_id.strip():
            filter_metadata = {"source": source_id}
        
        if use_hybrid_search:
            # Hybrid search: combine vector and keyword search
            
            # Import the search function from utils
            from utils import search_code_examples as search_code_examples_impl
            
            # 1. Get vector search results (get more to account for filtering)
            vector_results = search_code_examples_impl(
                client=supabase_client,
                query=query,
                match_count=match_count * 2,  # Get double to have room for filtering
                filter_metadata=filter_metadata
            )
            
            # 2. Get keyword search results using ILIKE on both content and summary
            keyword_query = supabase_client.from_('code_examples')\
                .select('id, url, chunk_number, content, summary, metadata, source_id')\
                .or_(f'content.ilike.%{query}%,summary.ilike.%{query}%')
            
            # Apply source filter if provided
            if source_id and source_id.strip():
                keyword_query = keyword_query.eq('source_id', source_id)
            
            # Execute keyword search
            keyword_response = keyword_query.limit(match_count * 2).execute()
            keyword_results = keyword_response.data if keyword_response.data else []
            
            # 3. Combine results with preference for items appearing in both
            seen_ids = set()
            combined_results = []
            
            # First, add items that appear in both searches (these are the best matches)
            vector_ids = {r.get('id') for r in vector_results if r.get('id')}
            for kr in keyword_results:
                if kr['id'] in vector_ids and kr['id'] not in seen_ids:
                    # Find the vector result to get similarity score
                    for vr in vector_results:
                        if vr.get('id') == kr['id']:
                            # Boost similarity score for items in both results
                            vr['similarity'] = min(1.0, vr.get('similarity', 0) * 1.2)
                            combined_results.append(vr)
                            seen_ids.add(kr['id'])
                            break
            
            # Then add remaining vector results (semantic matches without exact keyword)
            for vr in vector_results:
                if vr.get('id') and vr['id'] not in seen_ids and len(combined_results) < match_count:
                    combined_results.append(vr)
                    seen_ids.add(vr['id'])
            
            # Finally, add pure keyword matches if we still need more results
            for kr in keyword_results:
                if kr['id'] not in seen_ids and len(combined_results) < match_count:
                    # Convert keyword result to match vector result format
                    combined_results.append({
                        'id': kr['id'],
                        'url': kr['url'],
                        'chunk_number': kr['chunk_number'],
                        'content': kr['content'],
                        'summary': kr['summary'],
                        'metadata': kr['metadata'],
                        'source_id': kr['source_id'],
                        'similarity': 0.5  # Default similarity for keyword-only matches
                    })
                    seen_ids.add(kr['id'])
            
            # Use combined results
            results = combined_results[:match_count]
            
        else:
            # Standard vector search only
            from utils import search_code_examples as search_code_examples_impl
            
            results = search_code_examples_impl(
                client=supabase_client,
                query=query,
                match_count=match_count,
                filter_metadata=filter_metadata
            )
        
        # Apply reranking if enabled
        use_reranking = os.getenv("USE_RERANKING", "false") == "true"
        if use_reranking and ctx.request_context.lifespan_context.reranking_model:
            results = rerank_results(ctx.request_context.lifespan_context.reranking_model, query, results, content_key="content")
        
        # Format the results
        formatted_results = []
        for result in results:
            formatted_result = {
                "url": result.get("url"),
                "code": result.get("content"),
                "summary": result.get("summary"),
                "metadata": result.get("metadata"),
                "source_id": result.get("source_id"),
                "similarity": result.get("similarity")
            }
            # Include rerank score if available
            if "rerank_score" in result:
                formatted_result["rerank_score"] = result["rerank_score"]
            formatted_results.append(formatted_result)
        
        return json.dumps({
            "success": True,
            "query": query,
            "source_filter": source_id,
            "search_mode": "hybrid" if use_hybrid_search else "vector",
            "reranking_applied": use_reranking and ctx.request_context.lifespan_context.reranking_model is not None,
            "results": formatted_results,
            "count": len(formatted_results)
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "query": query,
            "error": str(e)
        }, indent=2)

@mcp.tool()
async def check_ai_script_hallucinations(ctx: Context, script_path: str) -> str:
    """
    Check an AI-generated Python script for hallucinations using the knowledge graph.
    
    This tool analyzes a Python script for potential AI hallucinations by validating
    imports, method calls, class instantiations, and function calls against a Neo4j
    knowledge graph containing real repository data.
    
    The tool performs comprehensive analysis including:
    - Import validation against known repositories
    - Method call validation on classes from the knowledge graph
    - Class instantiation parameter validation
    - Function call parameter validation
    - Attribute access validation
    
    Args:
        script_path: Absolute path to the Python script to analyze
    
    Returns:
        JSON string with hallucination detection results, confidence scores, and recommendations
    """
    try:
        # Check if knowledge graph functionality is enabled
        knowledge_graph_enabled = os.getenv("USE_KNOWLEDGE_GRAPH", "false") == "true"
        if not knowledge_graph_enabled:
            return json.dumps({
                "success": False,
                "error": "Knowledge graph functionality is disabled. Set USE_KNOWLEDGE_GRAPH=true in environment."
            }, indent=2)
        
        # Get the knowledge validator from context
        knowledge_validator = ctx.request_context.lifespan_context.knowledge_validator
        
        if not knowledge_validator:
            return json.dumps({
                "success": False,
                "error": "Knowledge graph validator not available. Check Neo4j configuration in environment variables."
            }, indent=2)
        
        # Validate script path
        validation = validate_script_path(script_path)
        if not validation["valid"]:
            return json.dumps({
                "success": False,
                "script_path": script_path,
                "error": validation["error"]
            }, indent=2)
        
        # Step 1: Analyze script structure using AST
        analyzer = AIScriptAnalyzer()
        analysis_result = analyzer.analyze_script(script_path)
        
        if analysis_result.errors:
            print(f"Analysis warnings for {script_path}: {analysis_result.errors}")
        
        # Step 2: Validate against knowledge graph
        validation_result = await knowledge_validator.validate_script(analysis_result)
        
        # Step 3: Generate comprehensive report
        reporter = HallucinationReporter()
        report = reporter.generate_comprehensive_report(validation_result)
        
        # Format response with comprehensive information
        return json.dumps({
            "success": True,
            "script_path": script_path,
            "overall_confidence": validation_result.overall_confidence,
            "validation_summary": {
                "total_validations": report["validation_summary"]["total_validations"],
                "valid_count": report["validation_summary"]["valid_count"],
                "invalid_count": report["validation_summary"]["invalid_count"],
                "uncertain_count": report["validation_summary"]["uncertain_count"],
                "not_found_count": report["validation_summary"]["not_found_count"],
                "hallucination_rate": report["validation_summary"]["hallucination_rate"]
            },
            "hallucinations_detected": report["hallucinations_detected"],
            "recommendations": report["recommendations"],
            "analysis_metadata": {
                "total_imports": report["analysis_metadata"]["total_imports"],
                "total_classes": report["analysis_metadata"]["total_classes"],
                "total_methods": report["analysis_metadata"]["total_methods"],
                "total_attributes": report["analysis_metadata"]["total_attributes"],
                "total_functions": report["analysis_metadata"]["total_functions"]
            },
            "libraries_analyzed": report.get("libraries_analyzed", [])
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "script_path": script_path,
            "error": f"Analysis failed: {str(e)}"
        }, indent=2)

@mcp.tool()
async def query_knowledge_graph(ctx: Context, command: str) -> str:
    """
    Query and explore the Neo4j knowledge graph containing repository data.
    
    This tool provides comprehensive access to the knowledge graph for exploring repositories,
    classes, methods, functions, and their relationships. Perfect for understanding what data
    is available for hallucination detection and debugging validation results.
    
    **⚠️ IMPORTANT: Always start with the `repos` command first!**
    Before using any other commands, run `repos` to see what repositories are available
    in your knowledge graph. This will help you understand what data you can explore.
    
    ## Available Commands:
    
    **Repository Commands:**
    - `repos` - **START HERE!** List all repositories in the knowledge graph
    - `explore <repo_name>` - Get detailed overview of a specific repository
    
    **Class Commands:**  
    - `classes` - List all classes across all repositories (limited to 20)
    - `classes <repo_name>` - List classes in a specific repository
    - `class <class_name>` - Get detailed information about a specific class including methods and attributes
    
    **Method Commands:**
    - `method <method_name>` - Search for methods by name across all classes
    - `method <method_name> <class_name>` - Search for a method within a specific class
    
    **Custom Query:**
    - `query <cypher_query>` - Execute a custom Cypher query (results limited to 20 records)
    
    ## Knowledge Graph Schema:
    
    **Node Types:**
    - Repository: `(r:Repository {name: string})`
    - File: `(f:File {path: string, module_name: string})`
    - Class: `(c:Class {name: string, full_name: string})`
    - Method: `(m:Method {name: string, params_list: [string], params_detailed: [string], return_type: string, args: [string]})`
    - Function: `(func:Function {name: string, params_list: [string], params_detailed: [string], return_type: string, args: [string]})`
    - Attribute: `(a:Attribute {name: string, type: string})`
    
    **Relationships:**
    - `(r:Repository)-[:CONTAINS]->(f:File)`
    - `(f:File)-[:DEFINES]->(c:Class)`
    - `(c:Class)-[:HAS_METHOD]->(m:Method)`
    - `(c:Class)-[:HAS_ATTRIBUTE]->(a:Attribute)`
    - `(f:File)-[:DEFINES]->(func:Function)`
    
    ## Example Workflow:
    ```
    1. repos                                    # See what repositories are available
    2. explore pydantic-ai                      # Explore a specific repository
    3. classes pydantic-ai                      # List classes in that repository
    4. class Agent                              # Explore the Agent class
    5. method run_stream                        # Search for run_stream method
    6. method __init__ Agent                    # Find Agent constructor
    7. query "MATCH (c:Class)-[:HAS_METHOD]->(m:Method) WHERE m.name = 'run' RETURN c.name, m.name LIMIT 5"
    ```
    
    Args:
        command: Command string to execute (see available commands above)
    
    Returns:
        JSON string with query results, statistics, and metadata
    """
    try:
        # Check if knowledge graph functionality is enabled
        knowledge_graph_enabled = os.getenv("USE_KNOWLEDGE_GRAPH", "false") == "true"
        if not knowledge_graph_enabled:
            return json.dumps({
                "success": False,
                "error": "Knowledge graph functionality is disabled. Set USE_KNOWLEDGE_GRAPH=true in environment."
            }, indent=2)
        
        # Get Neo4j driver from context
        repo_extractor = ctx.request_context.lifespan_context.repo_extractor
        if not repo_extractor or not repo_extractor.driver:
            return json.dumps({
                "success": False,
                "error": "Neo4j connection not available. Check Neo4j configuration in environment variables."
            }, indent=2)
        
        # Parse command
        command = command.strip()
        if not command:
            return json.dumps({
                "success": False,
                "command": "",
                "error": "Command cannot be empty. Available commands: repos, explore <repo>, classes [repo], class <name>, method <name> [class], query <cypher>"
            }, indent=2)
        
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        async with repo_extractor.driver.session() as session:
            # Route to appropriate handler
            if cmd == "repos":
                return await _handle_repos_command(session, command)
            elif cmd == "explore":
                if not args:
                    return json.dumps({
                        "success": False,
                        "command": command,
                        "error": "Repository name required. Usage: explore <repo_name>"
                    }, indent=2)
                return await _handle_explore_command(session, command, args[0])
            elif cmd == "classes":
                repo_name = args[0] if args else None
                return await _handle_classes_command(session, command, repo_name)
            elif cmd == "class":
                if not args:
                    return json.dumps({
                        "success": False,
                        "command": command,
                        "error": "Class name required. Usage: class <class_name>"
                    }, indent=2)
                return await _handle_class_command(session, command, args[0])
            elif cmd == "method":
                if not args:
                    return json.dumps({
                        "success": False,
                        "command": command,
                        "error": "Method name required. Usage: method <method_name> [class_name]"
                    }, indent=2)
                method_name = args[0]
                class_name = args[1] if len(args) > 1 else None
                return await _handle_method_command(session, command, method_name, class_name)
            elif cmd == "query":
                if not args:
                    return json.dumps({
                        "success": False,
                        "command": command,
                        "error": "Cypher query required. Usage: query <cypher_query>"
                    }, indent=2)
                cypher_query = " ".join(args)
                return await _handle_query_command(session, command, cypher_query)
            else:
                return json.dumps({
                    "success": False,
                    "command": command,
                    "error": f"Unknown command '{cmd}'. Available commands: repos, explore <repo>, classes [repo], class <name>, method <name> [class], query <cypher>"
                }, indent=2)
                
    except Exception as e:
        return json.dumps({
            "success": False,
            "command": command,
            "error": f"Query execution failed: {str(e)}"
        }, indent=2)


async def _handle_repos_command(session, command: str) -> str:
    """Handle 'repos' command - list all repositories"""
    query = "MATCH (r:Repository) RETURN r.name as name ORDER BY r.name"
    result = await session.run(query)
    
    repos = []
    async for record in result:
        repos.append(record['name'])
    
    return json.dumps({
        "success": True,
        "command": command,
        "data": {
            "repositories": repos
        },
        "metadata": {
            "total_results": len(repos),
            "limited": False
        }
    }, indent=2)


async def _handle_explore_command(session, command: str, repo_name: str) -> str:
    """Handle 'explore <repo>' command - get repository overview"""
    # Check if repository exists
    repo_check_query = "MATCH (r:Repository {name: $repo_name}) RETURN r.name as name"
    result = await session.run(repo_check_query, repo_name=repo_name)
    repo_record = await result.single()
    
    if not repo_record:
        return json.dumps({
            "success": False,
            "command": command,
            "error": f"Repository '{repo_name}' not found in knowledge graph"
        }, indent=2)
    
    # Get file count
    files_query = """
    MATCH (r:Repository {name: $repo_name})-[:CONTAINS]->(f:File)
    RETURN count(f) as file_count
    """
    result = await session.run(files_query, repo_name=repo_name)
    file_count = (await result.single())['file_count']
    
    # Get class count
    classes_query = """
    MATCH (r:Repository {name: $repo_name})-[:CONTAINS]->(f:File)-[:DEFINES]->(c:Class)
    RETURN count(DISTINCT c) as class_count
    """
    result = await session.run(classes_query, repo_name=repo_name)
    class_count = (await result.single())['class_count']
    
    # Get function count
    functions_query = """
    MATCH (r:Repository {name: $repo_name})-[:CONTAINS]->(f:File)-[:DEFINES]->(func:Function)
    RETURN count(DISTINCT func) as function_count
    """
    result = await session.run(functions_query, repo_name=repo_name)
    function_count = (await result.single())['function_count']
    
    # Get method count
    methods_query = """
    MATCH (r:Repository {name: $repo_name})-[:CONTAINS]->(f:File)-[:DEFINES]->(c:Class)-[:HAS_METHOD]->(m:Method)
    RETURN count(DISTINCT m) as method_count
    """
    result = await session.run(methods_query, repo_name=repo_name)
    method_count = (await result.single())['method_count']
    
    return json.dumps({
        "success": True,
        "command": command,
        "data": {
            "repository": repo_name,
            "statistics": {
                "files": file_count,
                "classes": class_count,
                "functions": function_count,
                "methods": method_count
            }
        },
        "metadata": {
            "total_results": 1,
            "limited": False
        }
    }, indent=2)


async def _handle_classes_command(session, command: str, repo_name: str = None) -> str:
    """Handle 'classes [repo]' command - list classes"""
    limit = 20
    
    if repo_name:
        query = """
        MATCH (r:Repository {name: $repo_name})-[:CONTAINS]->(f:File)-[:DEFINES]->(c:Class)
        RETURN c.name as name, c.full_name as full_name
        ORDER BY c.name
        LIMIT $limit
        """
        result = await session.run(query, repo_name=repo_name, limit=limit)
    else:
        query = """
        MATCH (c:Class)
        RETURN c.name as name, c.full_name as full_name
        ORDER BY c.name
        LIMIT $limit
        """
        result = await session.run(query, limit=limit)
    
    classes = []
    async for record in result:
        classes.append({
            'name': record['name'],
            'full_name': record['full_name']
        })
    
    return json.dumps({
        "success": True,
        "command": command,
        "data": {
            "classes": classes,
            "repository_filter": repo_name
        },
        "metadata": {
            "total_results": len(classes),
            "limited": len(classes) >= limit
        }
    }, indent=2)


async def _handle_class_command(session, command: str, class_name: str) -> str:
    """Handle 'class <name>' command - explore specific class"""
    # Find the class
    class_query = """
    MATCH (c:Class)
    WHERE c.name = $class_name OR c.full_name = $class_name
    RETURN c.name as name, c.full_name as full_name
    LIMIT 1
    """
    result = await session.run(class_query, class_name=class_name)
    class_record = await result.single()
    
    if not class_record:
        return json.dumps({
            "success": False,
            "command": command,
            "error": f"Class '{class_name}' not found in knowledge graph"
        }, indent=2)
    
    actual_name = class_record['name']
    full_name = class_record['full_name']
    
    # Get methods
    methods_query = """
    MATCH (c:Class)-[:HAS_METHOD]->(m:Method)
    WHERE c.name = $class_name OR c.full_name = $class_name
    RETURN m.name as name, m.params_list as params_list, m.params_detailed as params_detailed, m.return_type as return_type
    ORDER BY m.name
    """
    result = await session.run(methods_query, class_name=class_name)
    
    methods = []
    async for record in result:
        # Use detailed params if available, fall back to simple params
        params_to_use = record['params_detailed'] or record['params_list'] or []
        methods.append({
            'name': record['name'],
            'parameters': params_to_use,
            'return_type': record['return_type'] or 'Any'
        })
    
    # Get attributes
    attributes_query = """
    MATCH (c:Class)-[:HAS_ATTRIBUTE]->(a:Attribute)
    WHERE c.name = $class_name OR c.full_name = $class_name
    RETURN a.name as name, a.type as type
    ORDER BY a.name
    """
    result = await session.run(attributes_query, class_name=class_name)
    
    attributes = []
    async for record in result:
        attributes.append({
            'name': record['name'],
            'type': record['type'] or 'Any'
        })
    
    return json.dumps({
        "success": True,
        "command": command,
        "data": {
            "class": {
                "name": actual_name,
                "full_name": full_name,
                "methods": methods,
                "attributes": attributes
            }
        },
        "metadata": {
            "total_results": 1,
            "methods_count": len(methods),
            "attributes_count": len(attributes),
            "limited": False
        }
    }, indent=2)


async def _handle_method_command(session, command: str, method_name: str, class_name: str = None) -> str:
    """Handle 'method <name> [class]' command - search for methods"""
    if class_name:
        query = """
        MATCH (c:Class)-[:HAS_METHOD]->(m:Method)
        WHERE (c.name = $class_name OR c.full_name = $class_name)
          AND m.name = $method_name
        RETURN c.name as class_name, c.full_name as class_full_name,
               m.name as method_name, m.params_list as params_list, 
               m.params_detailed as params_detailed, m.return_type as return_type, m.args as args
        """
        result = await session.run(query, class_name=class_name, method_name=method_name)
    else:
        query = """
        MATCH (c:Class)-[:HAS_METHOD]->(m:Method)
        WHERE m.name = $method_name
        RETURN c.name as class_name, c.full_name as class_full_name,
               m.name as method_name, m.params_list as params_list, 
               m.params_detailed as params_detailed, m.return_type as return_type, m.args as args
        ORDER BY c.name
        LIMIT 20
        """
        result = await session.run(query, method_name=method_name)
    
    methods = []
    async for record in result:
        # Use detailed params if available, fall back to simple params
        params_to_use = record['params_detailed'] or record['params_list'] or []
        methods.append({
            'class_name': record['class_name'],
            'class_full_name': record['class_full_name'],
            'method_name': record['method_name'],
            'parameters': params_to_use,
            'return_type': record['return_type'] or 'Any',
            'legacy_args': record['args'] or []
        })
    
    if not methods:
        return json.dumps({
            "success": False,
            "command": command,
            "error": f"Method '{method_name}'" + (f" in class '{class_name}'" if class_name else "") + " not found"
        }, indent=2)
    
    return json.dumps({
        "success": True,
        "command": command,
        "data": {
            "methods": methods,
            "class_filter": class_name
        },
        "metadata": {
            "total_results": len(methods),
            "limited": len(methods) >= 20 and not class_name
        }
    }, indent=2)


async def _handle_query_command(session, command: str, cypher_query: str) -> str:
    """Handle 'query <cypher>' command - execute custom Cypher query"""
    try:
        # Execute the query with a limit to prevent overwhelming responses
        result = await session.run(cypher_query)
        
        records = []
        count = 0
        async for record in result:
            records.append(dict(record))
            count += 1
            if count >= 20:  # Limit results to prevent overwhelming responses
                break
        
        return json.dumps({
            "success": True,
            "command": command,
            "data": {
                "query": cypher_query,
                "results": records
            },
            "metadata": {
                "total_results": len(records),
                "limited": len(records) >= 20
            }
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "command": command,
            "error": f"Cypher query error: {str(e)}",
            "data": {
                "query": cypher_query
            }
        }, indent=2)


@mcp.tool()
async def parse_github_repository(ctx: Context, repo_url: str) -> str:
    """
    Parse a GitHub repository into the Neo4j knowledge graph.
    
    This tool clones a GitHub repository, analyzes its Python files, and stores
    the code structure (classes, methods, functions, imports) in Neo4j for use
    in hallucination detection. The tool:
    
    - Clones the repository to a temporary location
    - Analyzes Python files to extract code structure
    - Stores classes, methods, functions, and imports in Neo4j
    - Provides detailed statistics about the parsing results
    - Automatically handles module name detection for imports
    
    Args:
        repo_url: GitHub repository URL (e.g., 'https://github.com/user/repo.git')
    
    Returns:
        JSON string with parsing results, statistics, and repository information
    """
    try:
        # Check if knowledge graph functionality is enabled
        knowledge_graph_enabled = os.getenv("USE_KNOWLEDGE_GRAPH", "false") == "true"
        if not knowledge_graph_enabled:
            return json.dumps({
                "success": False,
                "error": "Knowledge graph functionality is disabled. Set USE_KNOWLEDGE_GRAPH=true in environment."
            }, indent=2)
        
        # Get the repository extractor from context
        repo_extractor = ctx.request_context.lifespan_context.repo_extractor
        
        if not repo_extractor:
            return json.dumps({
                "success": False,
                "error": "Repository extractor not available. Check Neo4j configuration in environment variables."
            }, indent=2)
        
        # Validate repository URL
        validation = validate_github_url(repo_url)
        if not validation["valid"]:
            return json.dumps({
                "success": False,
                "repo_url": repo_url,
                "error": validation["error"]
            }, indent=2)
        
        repo_name = validation["repo_name"]
        
        # Parse the repository (this includes cloning, analysis, and Neo4j storage)
        print(f"Starting repository analysis for: {repo_name}")
        await repo_extractor.analyze_repository(repo_url)
        print(f"Repository analysis completed for: {repo_name}")
        
        # Query Neo4j for statistics about the parsed repository
        async with repo_extractor.driver.session() as session:
            # Get comprehensive repository statistics
            stats_query = """
            MATCH (r:Repository {name: $repo_name})
            OPTIONAL MATCH (r)-[:CONTAINS]->(f:File)
            OPTIONAL MATCH (f)-[:DEFINES]->(c:Class)
            OPTIONAL MATCH (c)-[:HAS_METHOD]->(m:Method)
            OPTIONAL MATCH (f)-[:DEFINES]->(func:Function)
            OPTIONAL MATCH (c)-[:HAS_ATTRIBUTE]->(a:Attribute)
            WITH r, 
                 count(DISTINCT f) as files_count,
                 count(DISTINCT c) as classes_count,
                 count(DISTINCT m) as methods_count,
                 count(DISTINCT func) as functions_count,
                 count(DISTINCT a) as attributes_count
            
            // Get some sample module names
            OPTIONAL MATCH (r)-[:CONTAINS]->(sample_f:File)
            WITH r, files_count, classes_count, methods_count, functions_count, attributes_count,
                 collect(DISTINCT sample_f.module_name)[0..5] as sample_modules
            
            RETURN 
                r.name as repo_name,
                files_count,
                classes_count, 
                methods_count,
                functions_count,
                attributes_count,
                sample_modules
            """
            
            result = await session.run(stats_query, repo_name=repo_name)
            record = await result.single()
            
            if record:
                stats = {
                    "repository": record['repo_name'],
                    "files_processed": record['files_count'],
                    "classes_created": record['classes_count'],
                    "methods_created": record['methods_count'], 
                    "functions_created": record['functions_count'],
                    "attributes_created": record['attributes_count'],
                    "sample_modules": record['sample_modules'] or []
                }
            else:
                return json.dumps({
                    "success": False,
                    "repo_url": repo_url,
                    "error": f"Repository '{repo_name}' not found in database after parsing"
                }, indent=2)
        
        return json.dumps({
            "success": True,
            "repo_url": repo_url,
            "repo_name": repo_name,
            "message": f"Successfully parsed repository '{repo_name}' into knowledge graph",
            "statistics": stats,
            "ready_for_validation": True,
            "next_steps": [
                "Repository is now available for hallucination detection",
                f"Use check_ai_script_hallucinations to validate scripts against {repo_name}",
                "The knowledge graph contains classes, methods, and functions from this repository"
            ]
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "repo_url": repo_url,
            "error": f"Repository parsing failed: {str(e)}"
        }, indent=2)

async def crawl_markdown_file(crawler: AsyncWebCrawler, url: str) -> List[Dict[str, Any]]:
    """
    Crawl a .txt or markdown file.
    
    Args:
        crawler: AsyncWebCrawler instance
        url: URL of the file
        
    Returns:
        List of dictionaries with URL and markdown content
    """
    crawl_config = CrawlerRunConfig()

    result = await crawler.arun(url=url, config=crawl_config)
    if result.success and result.markdown:
        return [{'url': url, 'markdown': result.markdown}]
    else:
        print(f"Failed to crawl {url}: {result.error_message}")
        return []

async def crawl_batch(crawler: AsyncWebCrawler, urls: List[str], max_concurrent: int = 10) -> List[Dict[str, Any]]:
    """
    Batch crawl multiple URLs in parallel.
    
    Args:
        crawler: AsyncWebCrawler instance
        urls: List of URLs to crawl
        max_concurrent: Maximum number of concurrent browser sessions
        
    Returns:
        List of dictionaries with URL and markdown content
    """
    crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, stream=False)
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=70.0,
        check_interval=1.0,
        max_session_permit=max_concurrent
    )

    results = await crawler.arun_many(urls=urls, config=crawl_config, dispatcher=dispatcher)
    return [{'url': r.url, 'markdown': r.markdown, 'links': r.links} for r in results if r.success and r.markdown]

async def crawl_recursive_internal_links(crawler: AsyncWebCrawler, start_urls: List[str], max_depth: int = 3, max_concurrent: int = 10) -> List[Dict[str, Any]]:
    """
    Recursively crawl internal links from start URLs up to a maximum depth.
    
    Args:
        crawler: AsyncWebCrawler instance
        start_urls: List of starting URLs
        max_depth: Maximum recursion depth
        max_concurrent: Maximum number of concurrent browser sessions
        
    Returns:
        List of dictionaries with URL and markdown content
    """
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, stream=False)
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=70.0,
        check_interval=1.0,
        max_session_permit=max_concurrent
    )

    visited = set()

    def normalize_url(url):
        return urldefrag(url)[0]

    current_urls = set([normalize_url(u) for u in start_urls])
    results_all = []

    for depth in range(max_depth):
        urls_to_crawl = [normalize_url(url) for url in current_urls if normalize_url(url) not in visited]
        if not urls_to_crawl:
            break

        results = await crawler.arun_many(urls=urls_to_crawl, config=run_config, dispatcher=dispatcher)
        next_level_urls = set()

        for result in results:
            norm_url = normalize_url(result.url)
            visited.add(norm_url)

            if result.success and result.markdown:
                results_all.append({'url': result.url, 'markdown': result.markdown})
                for link in result.links.get("internal", []):
                    next_url = normalize_url(link["href"])
                    if next_url not in visited:
                        next_level_urls.add(next_url)

        current_urls = next_level_urls

    return results_all

async def main():
    import uvicorn
    import asyncio
    
    # Configure logging
    from src.config import configure_logging
    configure_logging()
    
    logger = logging.getLogger("http_api")
    logger.info("Starting Crawl4AI MCP HTTP API server...")
    
    # Get port from environment or default
    port = int(os.getenv("PORT", "8051"))
    host = os.getenv("HOST", "0.0.0.0")
    
    # Run both MCP and HTTP servers
    transport = os.getenv("TRANSPORT", "sse")
    
    if transport == 'sse':
        # For SSE transport, we run the FastAPI app which includes both MCP and custom endpoints
        try:
            logger.info(f"Starting FastAPI server with MCP support on {host}:{port}")
            
            # Run the FastMCP SSE server which includes our custom endpoints
            config = uvicorn.Config(
                app=sse_app,
                host=host,
                port=port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()
        except Exception as e:
            logger.error(f"Failed to start FastAPI server: {e}")
            raise
        
    else:
        # Run the MCP server with stdio transport only
        await mcp.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())