"""
Utils package for Crawl4AI MCP server.
"""

# Import functions from utils modules
from .cache import *
from .http_helpers import *

# Re-export main utils functions to maintain backward compatibility
import sys
from pathlib import Path

# Add parent directory to path to import from main utils.py
utils_path = Path(__file__).resolve().parent.parent / 'utils.py'
if utils_path.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("main_utils", utils_path)
    main_utils = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_utils)
    
    # Export functions from main utils
    get_supabase_client = main_utils.get_supabase_client
    add_documents_to_supabase = main_utils.add_documents_to_supabase
    search_documents = main_utils.search_documents
    extract_code_blocks = main_utils.extract_code_blocks
    generate_code_example_summary = main_utils.generate_code_example_summary
    add_code_examples_to_supabase = main_utils.add_code_examples_to_supabase
    update_source_info = main_utils.update_source_info
    extract_source_summary = main_utils.extract_source_summary
    search_code_examples = main_utils.search_code_examples
    create_embedding = main_utils.create_embedding
    create_embeddings_batch = main_utils.create_embeddings_batch
    generate_contextual_embedding = main_utils.generate_contextual_embedding
    process_chunk_with_context = main_utils.process_chunk_with_context

__all__ = [
    'get_supabase_client',
    'add_documents_to_supabase', 
    'search_documents',
    'extract_code_blocks',
    'generate_code_example_summary',
    'add_code_examples_to_supabase',
    'update_source_info',
    'extract_source_summary',
    'search_code_examples',
    'create_embedding',
    'create_embeddings_batch',
    'generate_contextual_embedding',
    'process_chunk_with_context'
]