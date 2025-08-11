import React, { useState, useEffect } from 'react';
import mcpService from '../services/mcpService';
import './Dashboard.css';

const Dashboard = () => {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchSources();
  }, []);

  const fetchSources = async () => {
    try {
      setLoading(true);
      const result = await mcpService.getAvailableSources();
      if (result.error) {
        setError(result.error);
      } else {
        setSources(result.data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard">
      <h2>Dashboard</h2>
      
      {loading && <p>Loading dashboard data...</p>}
      
      {error && (
        <div className="error-message">
          <p>Error loading dashboard data: {error}</p>
          <p>This is expected as the integration is not yet complete.</p>
        </div>
      )}
      
      <div className="dashboard-stats">
        <div className="stat-card">
          <h3>Total Sources</h3>
          <p className="stat-value">{sources.length}</p>
        </div>
        
        <div className="stat-card">
          <h3>Total Documents</h3>
          <p className="stat-value">0</p>
          <p className="stat-note">Not yet implemented</p>
        </div>
        
        <div className="stat-card">
          <h3>Code Examples</h3>
          <p className="stat-value">0</p>
          <p className="stat-note">Not yet implemented</p>
        </div>
      </div>
      
      <div className="quick-actions">
        <h3>Quick Actions</h3>
        <div className="action-buttons">
          <button className="action-button" disabled>
            Search Documents
          </button>
          <button className="action-button" disabled>
            Browse Sources
          </button>
          <button className="action-button" disabled>
            View Code Examples
          </button>
        </div>
      </div>
      
      <div className="development-note">
        <h3>Development Status</h3>
        <p>This is a work in progress. The following features are planned:</p>
        <ul>
          <li>Complete integration with MCP server tools</li>
          <li>Document explorer with search and filtering</li>
          <li>Source management interface</li>
          <li>Semantic search using RAG capabilities</li>
          <li>Code example browser (conditional)</li>
          <li>Data visualization features</li>
        </ul>
      </div>
    </div>
  );
};

export default Dashboard;