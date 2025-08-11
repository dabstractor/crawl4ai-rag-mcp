import React, { useState, useEffect } from 'react';
import mcpService from '../services/mcpService';
import './ConnectionTest.css';

const ConnectionTest = () => {
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [testResults, setTestResults] = useState([]);
  const [isTesting, setIsTesting] = useState(false);

  useEffect(() => {
    // Check initial connection status on component mount
    updateConnectionStatus();
  }, []);

  const updateConnectionStatus = async () => {
    try {
      const result = await mcpService.testConnection();
      if (result.success) {
        setConnectionStatus('connected');
      } else {
        setConnectionStatus('error');
      }
    } catch (error) {
      setConnectionStatus('error');
    }
  };

  const handleConnect = async () => {
    try {
      const result = await mcpService.initializeConnection();
      await updateConnectionStatus();
      
      addTestResult({
        action: 'Connect',
        success: result.success,
        message: result.message || result.error,
        timestamp: new Date().toLocaleTimeString()
      });
    } catch (error) {
      addTestResult({
        action: 'Connect',
        success: false,
        message: error.message,
        timestamp: new Date().toLocaleTimeString()
      });
    }
  };

  const handleDisconnect = () => {
    mcpService.closeConnection();
    setConnectionStatus('disconnected');
    
    addTestResult({
      action: 'Disconnect',
      success: true,
      message: 'Connection closed successfully',
      timestamp: new Date().toLocaleTimeString()
    });
  };

  const handleTestGetSources = async () => {
    setIsTesting(true);
    try {
      const result = await mcpService.getAvailableSources();
      
      addTestResult({
        action: 'Get Sources',
        success: !result.error,
        message: result.error || `Found ${result.data?.length || 0} sources`,
        timestamp: new Date().toLocaleTimeString()
      });
    } catch (error) {
      addTestResult({
        action: 'Get Sources',
        success: false,
        message: error.message,
        timestamp: new Date().toLocaleTimeString()
      });
    } finally {
      setIsTesting(false);
    }
  };

  const addTestResult = (result) => {
    setTestResults(prev => [result, ...prev.slice(0, 9)]); // Keep only last 10 results
  };

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'green';
      case 'error': return 'red';
      default: return 'gray';
    }
  };

  return (
    <div className="connection-test">
      <h2>MCP Server Connection Test</h2>
      
      <div className="connection-status">
        <h3>Connection Status</h3>
        <div className="status-indicator">
          <span 
            className="status-dot" 
            style={{ backgroundColor: getStatusColor() }}
          ></span>
          <span className="status-text">{connectionStatus}</span>
        </div>
        
        <div className="connection-buttons">
          <button 
            onClick={handleConnect}
            disabled={connectionStatus === 'connected'}
          >
            Connect
          </button>
          <button 
            onClick={handleDisconnect}
            disabled={connectionStatus !== 'connected'}
          >
            Disconnect
          </button>
        </div>
      </div>
      
      <div className="test-actions">
        <h3>Test Actions</h3>
        <button 
          onClick={handleTestGetSources}
          disabled={connectionStatus !== 'connected' || isTesting}
        >
          {isTesting ? 'Testing...' : 'Test Get Sources'}
        </button>
      </div>
      
      <div className="test-results">
        <h3>Test Results</h3>
        {testResults.length === 0 ? (
          <p className="no-results">No test results yet</p>
        ) : (
          <div className="results-list">
            {testResults.map((result, index) => (
              <div 
                key={index} 
                className={`result-item ${result.success ? 'success' : 'error'}`}
              >
                <div className="result-header">
                  <span className="result-action">{result.action}</span>
                  <span className="result-time">{result.timestamp}</span>
                </div>
                <div className="result-message">{result.message}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ConnectionTest;