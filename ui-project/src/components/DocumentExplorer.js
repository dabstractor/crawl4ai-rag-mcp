import React, { useState, useEffect } from 'react';
import mcpService from '../services/mcpService';
import './DocumentExplorer.css';

const DocumentExplorer = () => {
  const [documents, setDocuments] = useState([]);
  const [filteredDocuments, setFilteredDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSource, setSelectedSource] = useState('');
  const [sortBy, setSortBy] = useState('date');
  const [sources, setSources] = useState([]);

  // Load documents and sources on component mount
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

  const loadDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // This would be implemented to fetch documents from the database
      // For now, we'll use mock data to demonstrate the UI
      const mockDocuments = [
        {
          id: '1',
          title: 'Introduction to Crawl4AI',
          url: 'https://docs.crawl4ai.com/introduction',
          source: 'docs.crawl4ai.com',
          date: '2024-01-15',
          wordCount: 1250,
          summary: 'An overview of the Crawl4AI framework and its capabilities for web crawling and data extraction.'
        },
        {
          id: '2',
          title: 'Advanced Configuration',
          url: 'https://docs.crawl4ai.com/advanced-config',
          source: 'docs.crawl4ai.com',
          date: '2024-01-20',
          wordCount: 2100,
          summary: 'Detailed guide on advanced configuration options for custom crawling scenarios.'
        },
        {
          id: '3',
          title: 'GitHub Repository Structure',
          url: 'https://github.com/crawl4ai/crawl4ai',
          source: 'github.com',
          date: '2024-01-10',
          wordCount: 850,
          summary: 'Overview of the Crawl4AI repository structure and key components.'
        }
      ];
      
      setDocuments(mockDocuments);
      setFilteredDocuments(mockDocuments);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (term) => {
    setSearchTerm(term);
    filterDocuments(term, selectedSource, sortBy);
  };

  const handleSourceFilter = (source) => {
    setSelectedSource(source);
    filterDocuments(searchTerm, source, sortBy);
  };

  const handleSort = (sortField) => {
    setSortBy(sortField);
    filterDocuments(searchTerm, selectedSource, sortField);
  };

  const filterDocuments = (term, source, sortField) => {
    let filtered = [...documents];
    
    // Apply search filter
    if (term) {
      filtered = filtered.filter(doc => 
        doc.title.toLowerCase().includes(term.toLowerCase()) ||
        doc.summary.toLowerCase().includes(term.toLowerCase()) ||
        doc.url.toLowerCase().includes(term.toLowerCase())
      );
    }
    
    // Apply source filter
    if (source) {
      filtered = filtered.filter(doc => doc.source === source);
    }
    
    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortField) {
        case 'title':
          return a.title.localeCompare(b.title);
        case 'source':
          return a.source.localeCompare(b.source);
        case 'date':
        default:
          return new Date(b.date) - new Date(a.date);
      }
    });
    
    setFilteredDocuments(filtered);
  };

  const clearFilters = () => {
    setSearchTerm('');
    setSelectedSource('');
    setSortBy('date');
    setFilteredDocuments(documents);
  };

  // Load documents when the component is first rendered
  useEffect(() => {
    loadDocuments();
  }, []);

  return (
    <div className="document-explorer">
      <h2>Document Explorer</h2>
      
      <div className="explorer-controls">
        <div className="search-container">
          <input
            type="text"
            placeholder="Search documents..."
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
          
          <select
            value={sortBy}
            onChange={(e) => handleSort(e.target.value)}
            className="sort-filter"
          >
            <option value="date">Sort by Date</option>
            <option value="title">Sort by Title</option>
            <option value="source">Sort by Source</option>
          </select>
          
          <button onClick={clearFilters} className="clear-filters">
            Clear Filters
          </button>
        </div>
      </div>
      
      {error && (
        <div className="error-message">
          <p>Error loading documents: {error}</p>
          <p>This is expected as the integration is not yet complete.</p>
        </div>
      )}
      
      {loading && (
        <div className="loading-message">
          <p>Loading documents...</p>
        </div>
      )}
      
      {!loading && (
        <div className="documents-grid">
          {filteredDocuments.length > 0 ? (
            filteredDocuments.map((doc) => (
              <div key={doc.id} className="document-card">
                <div className="document-header">
                  <h3 className="document-title">
                    <a href={doc.url} target="_blank" rel="noopener noreferrer">
                      {doc.title}
                    </a>
                  </h3>
                  <span className="document-source">{doc.source}</span>
                </div>
                
                <div className="document-meta">
                  <span className="document-date">{doc.date}</span>
                  <span className="document-word-count">{doc.wordCount} words</span>
                </div>
                
                <div className="document-summary">
                  {doc.summary}
                </div>
                
                <div className="document-actions">
                  <button className="action-button">
                    View Details
                  </button>
                  <button className="action-button">
                    Search in Document
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="no-documents">
              <p>No documents found matching your criteria.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DocumentExplorer;