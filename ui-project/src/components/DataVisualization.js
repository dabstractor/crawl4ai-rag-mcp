import React, { useState, useEffect } from 'react';
import mcpService from '../services/mcpService';
import './DataVisualization.css';

const DataVisualization = () => {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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
      } else {
        setSources(result.data || []);
      }
    } catch (err) {
      setError(err.message);
      setSources([]);
    } finally {
      setLoading(false);
    }
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

  // Calculate statistics for visualization
  const calculateStats = () => {
    if (sources.length === 0) return null;
    
    const totalSources = sources.length;
    const totalWords = sources.reduce((sum, source) => sum + (source.total_words || 0), 0);
    const totalDocuments = sources.reduce((sum, source) => sum + (source.document_count || 0), 0);
    
    // Source distribution by word count
    const sourceDistribution = sources
      .map(source => ({
        name: source.source_id,
        words: source.total_words || 0
      }))
      .sort((a, b) => b.words - a.words)
      .slice(0, 10); // Top 10 sources
    
    return {
      totalSources,
      totalWords,
      totalDocuments,
      sourceDistribution
    };
  };

  const stats = calculateStats();

  // Simple bar chart component
  const BarChart = ({ data, title, valueFormatter }) => {
    if (!data || data.length === 0) return null;
    
    const maxValue = Math.max(...data.map(item => item.words));
    
    return (
      <div className="chart-container">
        <h3>{title}</h3>
        <div className="bar-chart">
          {data.map((item, index) => (
            <div key={index} className="bar-item">
              <div 
                className="bar" 
                style={{ height: `${(item.words / maxValue) * 100}%` }}
              ></div>
              <div className="bar-label">
                <div className="bar-name">{item.name}</div>
                <div className="bar-value">{valueFormatter(item.words)}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="data-visualization">
      <h2>Data Visualization</h2>
      
      {error && (
        <div className="error-message">
          <p>Error loading visualization data: {error}</p>
          <p>This is expected as the integration is not yet complete.</p>
        </div>
      )}
      
      {loading && (
        <div className="loading-message">
          <p>Loading visualization data...</p>
        </div>
      )}
      
      {!loading && stats && (
        <div className="visualization-content">
          <div className="stats-grid">
            <div className="stat-card">
              <h3>Total Sources</h3>
              <p className="stat-value">{stats.totalSources}</p>
            </div>
            
            <div className="stat-card">
              <h3>Total Words</h3>
              <p className="stat-value">{formatNumber(stats.totalWords)}</p>
            </div>
            
            <div className="stat-card">
              <h3>Total Documents</h3>
              <p className="stat-value">{formatNumber(stats.totalDocuments)}</p>
            </div>
          </div>
          
          <BarChart 
            data={stats.sourceDistribution} 
            title="Top Sources by Word Count"
            valueFormatter={formatNumber}
          />
          
          <div className="info-note">
            <p>📊 More advanced visualizations will be added in future updates.</p>
            <p>🎨 This visualization uses mock data for demonstration purposes.</p>
          </div>
        </div>
      )}
      
      {!loading && !stats && !error && (
        <div className="no-data">
          <p>No data available for visualization.</p>
        </div>
      )}
    </div>
  );
};

export default DataVisualization;