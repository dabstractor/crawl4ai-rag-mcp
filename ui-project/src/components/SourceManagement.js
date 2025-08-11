import React, { useState, useEffect } from 'react';
import mcpService from '../services/mcpService';
import './SourceManagement.css';

const SourceManagement = () => {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredSources, setFilteredSources] = useState([]);

  // Load sources on component mount
  useEffect(() => {
    loadSources();
  }, []);

  const loadSources = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await mcpService.getAvailableSources();
      
      if (result.error) {
        setError(result.error);
        setSources([]);
        setFilteredSources([]);
      } else {
        const sourcesData = result.data || [];
        setSources(sourcesData);
        setFilteredSources(sourcesData);
      }
    } catch (err) {
      setError(err.message);
      setSources([]);
      setFilteredSources([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (term) => {
    setSearchTerm(term);
    filterSources(term);
  };

  const filterSources = (term) => {
    if (!term) {
      setFilteredSources(sources);
      return;
    }
    
    const filtered = sources.filter(source => 
      source.source_id.toLowerCase().includes(term.toLowerCase()) ||
      (source.summary && source.summary.toLowerCase().includes(term.toLowerCase()))
    );
    
    setFilteredSources(filtered);
  };

  const refreshSources = async () => {
    await loadSources();
  };

  const formatNumber = (num) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleDateString();
  };

  return (
    <div className="source-management">
      <div className="header">
        <h2>Source Management</h2>
        <div className="header-actions">
          <button onClick={refreshSources} className="refresh-button" disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>
      
      <div className="search-container">
        <input
          type="text"
          placeholder="Search sources..."
          value={searchTerm}
          onChange={(e) => handleSearch(e.target.value)}
          className="search-input"
          disabled={loading}
        />
      </div>
      
      {error && (
        <div className="error-message">
          <p>Error loading sources: {error}</p>
          <p>This is expected as the integration is not yet complete.</p>
        </div>
      )}
      
      {loading && (
        <div className="loading-message">
          <p>Loading sources...</p>
        </div>
      )}
      
      {!loading && (
        <div className="sources-grid">
          {filteredSources.length > 0 ? (
            filteredSources.map((source, index) => (
              <div key={index} className="source-card">
                <div className="source-header">
                  <h3 className="source-title">{source.source_id}</h3>
                  <span className="source-domain">
                    {source.source_id}
                  </span>
                </div>
                
                <div className="source-stats">
                  <div className="stat-item">
                    <span className="stat-label">Total Words</span>
                    <span className="stat-value">
                      {source.total_words ? formatNumber(source.total_words) : '0'}
                    </span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Documents</span>
                    <span className="stat-value">
                      {source.document_count ? formatNumber(source.document_count) : '0'}
                    </span>
                  </div>
                </div>
                
                {source.summary && (
                  <div className="source-summary">
                    <p>{source.summary}</p>
                  </div>
                )}
                
                <div className="source-meta">
                  <div className="meta-item">
                    <span className="meta-label">Created</span>
                    <span className="meta-value">{formatDate(source.created_at)}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Updated</span>
                    <span className="meta-value">{formatDate(source.updated_at)}</span>
                  </div>
                </div>
                
                <div className="source-actions">
                  <button className="action-button">
                    View Documents
                  </button>
                  <button className="action-button">
                    Crawl More
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="no-sources">
              <p>No sources found{searchTerm ? ` matching "${searchTerm}"` : ''}.</p>
              {searchTerm && (
                <button onClick={() => setSearchTerm('')} className="clear-search">
                  Clear search
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SourceManagement;