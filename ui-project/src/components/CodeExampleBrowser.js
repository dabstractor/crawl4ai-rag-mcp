import React, { useState, useEffect } from 'react';
import mcpService from '../services/mcpService';
import './CodeExampleBrowser.css';

const CodeExampleBrowser = () => {
  const [codeExamples, setCodeExamples] = useState([]);
  const [filteredExamples, setFilteredExamples] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSource, setSelectedSource] = useState('');
  const [sources, setSources] = useState([]);

  // Load sources on component mount
  useEffect(() => {
    loadSources();
  }, []);

  const loadSources = async () => {
    try {
      const result = await mcpService.getAvailableSources();
      if (!result.error) {
        setSources(result.data || []);
      }
    } catch (err) {
      console.error('Error loading sources:', err);
    }
  };

  const loadCodeExamples = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await mcpService.searchCodeExamples(
        searchTerm || '',
        selectedSource || null,
        20
      );
      
      if (result.error) {
        setError(result.error);
        setCodeExamples([]);
        setFilteredExamples([]);
      } else {
        const examplesData = result.data || [];
        setCodeExamples(examplesData);
        setFilteredExamples(examplesData);
      }
    } catch (err) {
      setError(err.message);
      setCodeExamples([]);
      setFilteredExamples([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (term) => {
    setSearchTerm(term);
    // In a real implementation, we would call loadCodeExamples() here
    // For now, we'll just filter mock data
    filterExamples(term, selectedSource);
  };

  const handleSourceFilter = (source) => {
    setSelectedSource(source);
    filterExamples(searchTerm, source);
  };

  const filterExamples = (term, source) => {
    // This would be handled by the API in a real implementation
    // For now, we'll use mock data
    const mockExamples = [
      {
        id: '1',
        title: 'Basic Web Scraping Example',
        content: `import crawl4ai\n\ncrawler = crawl4ai.WebCrawler()\ncrawler.warmup()\n\nresult = crawler.run(\n    url="https://example.com",\n    word_count_threshold=10\n)\nprint(result.markdown)`,
        language: 'python',
        source: 'docs.crawl4ai.com',
        url: 'https://docs.crawl4ai.com/examples/basic',
        summary: 'A simple example showing how to scrape a webpage and extract markdown content.'
      },
      {
        id: '2',
        title: 'Advanced Configuration',
        content: `crawler = crawl4ai.WebCrawler(\n    headless=False,\n    verbose=True,\n    turbo_mode=True\n)\n\ncrawler.warmup()\n\nresult = crawler.run(\n    url="https://example.com",\n    js_code="document.querySelector('button').click()",\n    wait_for="div.content"\n)`,
        language: 'python',
        source: 'docs.crawl4ai.com',
        url: 'https://docs.crawl4ai.com/examples/advanced',
        summary: 'Advanced configuration options for handling dynamic content and JavaScript interactions.'
      }
    ];
    
    let filtered = mockExamples;
    
    if (term) {
      filtered = filtered.filter(example => 
        example.title.toLowerCase().includes(term.toLowerCase()) ||
        example.content.toLowerCase().includes(term.toLowerCase()) ||
        example.summary.toLowerCase().includes(term.toLowerCase())
      );
    }
    
    if (source) {
      filtered = filtered.filter(example => example.source === source);
    }
    
    setFilteredExamples(filtered);
  };

  const clearFilters = () => {
    setSearchTerm('');
    setSelectedSource('');
    // In a real implementation, we would reload all examples
    // For now, we'll just show mock data
    const mockExamples = [
      {
        id: '1',
        title: 'Basic Web Scraping Example',
        content: `import crawl4ai\n\ncrawler = crawl4ai.WebCrawler()\ncrawler.warmup()\n\nresult = crawler.run(\n    url="https://example.com",\n    word_count_threshold=10\n)\nprint(result.markdown)`,
        language: 'python',
        source: 'docs.crawl4ai.com',
        url: 'https://docs.crawl4ai.com/examples/basic',
        summary: 'A simple example showing how to scrape a webpage and extract markdown content.'
      },
      {
        id: '2',
        title: 'Advanced Configuration',
        content: `crawler = crawl4ai.WebCrawler(\n    headless=False,\n    verbose=True,\n    turbo_mode=True\n)\n\ncrawler.warmup()\n\nresult = crawler.run(\n    url="https://example.com",\n    js_code="document.querySelector('button').click()",\n    wait_for="div.content"\n)`,
        language: 'python',
        source: 'docs.crawl4ai.com',
        url: 'https://docs.crawl4ai.com/examples/advanced',
        summary: 'Advanced configuration options for handling dynamic content and JavaScript interactions.'
      }
    ];
    setFilteredExamples(mockExamples);
  };

  // Load initial mock data
  useEffect(() => {
    const mockExamples = [
      {
        id: '1',
        title: 'Basic Web Scraping Example',
        content: `import crawl4ai\n\ncrawler = crawl4ai.WebCrawler()\ncrawler.warmup()\n\nresult = crawler.run(\n    url="https://example.com",\n    word_count_threshold=10\n)\nprint(result.markdown)`,
        language: 'python',
        source: 'docs.crawl4ai.com',
        url: 'https://docs.crawl4ai.com/examples/basic',
        summary: 'A simple example showing how to scrape a webpage and extract markdown content.'
      },
      {
        id: '2',
        title: 'Advanced Configuration',
        content: `crawler = crawl4ai.WebCrawler(\n    headless=False,\n    verbose=True,\n    turbo_mode=True\n)\n\ncrawler.warmup()\n\nresult = crawler.run(\n    url="https://example.com",\n    js_code="document.querySelector('button').click()",\n    wait_for="div.content"\n)`,
        language: 'python',
        source: 'docs.crawl4ai.com',
        url: 'https://docs.crawl4ai.com/examples/advanced',
        summary: 'Advanced configuration options for handling dynamic content and JavaScript interactions.'
      }
    ];
    setCodeExamples(mockExamples);
    setFilteredExamples(mockExamples);
  }, []);

  return (
    <div className="code-example-browser">
      <h2>Code Examples</h2>
      <p className="feature-note">
        This feature requires the Crawl4AI MCP server to be configured with <code>USE_AGENTIC_RAG=true</code>.
      </p>
      
      <div className="browser-controls">
        <div className="search-container">
          <input
            type="text"
            placeholder="Search code examples..."
            value={searchTerm}
            onChange={(e) => handleSearch(e.target.value)}
            className="search-input"
          />
        </div>
        
        <div className="filter-container">
          <select
            value={selectedSource}
            onChange={(e) => handleSourceFilter(e.target.value)}
            className="source-filter"
          >
            <option value="">All Sources</option>
            {sources.map((source, index) => (
              <option key={index} value={source.source_id}>
                {source.source_id}
              </option>
            ))}
          </select>
          
          <button onClick={clearFilters} className="clear-filters">
            Clear Filters
          </button>
        </div>
      </div>
      
      {error && (
        <div className="error-message">
          <p>Error loading code examples: {error}</p>
          <p>This is expected as the integration is not yet complete.</p>
        </div>
      )}
      
      {loading && (
        <div className="loading-message">
          <p>Loading code examples...</p>
        </div>
      )}
      
      {!loading && (
        <div className="examples-grid">
          {filteredExamples.length > 0 ? (
            filteredExamples.map((example) => (
              <div key={example.id} className="example-card">
                <div className="example-header">
                  <h3 className="example-title">{example.title}</h3>
                  <span className="example-source">{example.source}</span>
                </div>
                
                {example.summary && (
                  <div className="example-summary">
                    <p>{example.summary}</p>
                  </div>
                )}
                
                <div className="example-content">
                  <pre className="code-block">
                    <code className={`language-${example.language}`}>
                      {example.content}
                    </code>
                  </pre>
                </div>
                
                <div className="example-actions">
                  <button className="action-button">
                    Copy Code
                  </button>
                  <button className="action-button">
                    View Full Example
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="no-examples">
              <p>No code examples found matching your criteria.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CodeExampleBrowser;