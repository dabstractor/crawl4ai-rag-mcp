import React, { useState } from 'react';
import mcpService from '../services/mcpService';
import './SearchInterface.css';

const SearchInterface = () => {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedSource, setSelectedSource] = useState('');
  const [matchCount, setMatchCount] = useState(10);

  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }
    
    try {
      setIsLoading(true);
      setError(null);
      
      const result = await mcpService.performRagQuery(
        query.trim(),
        selectedSource || null,
        matchCount
      );
      
      if (result.error) {
        setError(result.error);
        setSearchResults([]);
      } else {
        setSearchResults(result.data || []);
      }
    } catch (err) {
      setError(err.message);
      setSearchResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearSearch = () => {
    setQuery('');
    setSearchResults([]);
    setError(null);
    setSelectedSource('');
  };

  return (
    <div className="search-interface">
      <h2>Semantic Search</h2>
      
      <form className="search-form" onSubmit={handleSearch}>
        <div className="search-input-group">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your search query..."
            className="search-input"
            disabled={isLoading}
          />
          <button 
            type="submit" 
            className="search-button"
            disabled={isLoading || !query.trim()}
          >
            {isLoading ? 'Searching...' : 'Search'}
          </button>
        </div>
        
        <div className="search-options">
          <div className="option-group">
            <label htmlFor="source-filter">Filter by Source:</label>
            <select
              id="source-filter"
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="source-select"
              disabled={isLoading}
            >
              <option value="">All Sources</option>
              <option value="example.com">example.com</option>
              <option value="docs.crawl4ai.com">docs.crawl4ai.com</option>
              <option value="github.com">github.com</option>
            </select>
          </div>
          
          <div className="option-group">
            <label htmlFor="match-count">Results to Show:</label>
            <select
              id="match-count"
              value={matchCount}
              onChange={(e) => setMatchCount(Number(e.target.value))}
              className="count-select"
              disabled={isLoading}
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
          </div>
          
          <button
            type="button"
            onClick={clearSearch}
            className="clear-button"
            disabled={isLoading}
          >
            Clear
          </button>
        </div>
      </form>
      
      {error && (
        <div className="search-error">
          <p>Error: {error}</p>
          <p>This is expected as the integration is not yet complete.</p>
        </div>
      )}
      
      {isLoading && (
        <div className="search-loading">
          <p>Searching for "{query}"...</p>
        </div>
      )}
      
      {searchResults.length > 0 && (
        <div className="search-results">
          <h3>Search Results ({searchResults.length} found)</h3>
          <div className="results-list">
            {searchResults.map((result, index) => (
              <div key={index} className="result-item">
                <div className="result-header">
                  <h4 className="result-title">
                    {result.title || `Result ${index + 1}`}
                  </h4>
                  {result.similarity_score && (
                    <span className="similarity-score">
                      Score: {result.similarity_score.toFixed(4)}
                    </span>
                  )}
                </div>
                
                {result.source && (
                  <div className="result-source">
                    Source: {result.source}
                  </div>
                )}
                
                {result.content && (
                  <div className="result-content">
                    {result.content.substring(0, 300)}
                    {result.content.length > 300 ? '...' : ''}
                  </div>
                )}
                
                {result.url && (
                  <div className="result-url">
                    <a href={result.url} target="_blank" rel="noopener noreferrer">
                      {result.url}
                    </a>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
      
      {!isLoading && !error && searchResults.length === 0 && query && (
        <div className="no-results">
          <p>No results found for "{query}".</p>
        </div>
      )}
    </div>
  );
};

export default SearchInterface;