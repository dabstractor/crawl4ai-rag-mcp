import React, { useState } from 'react';
import './App.css';
import Navigation from './components/Navigation';
import Dashboard from './components/Dashboard';
import SearchInterface from './components/SearchInterface';
import DocumentExplorer from './components/DocumentExplorer';
import SourceManagement from './components/SourceManagement';
import CodeExampleBrowser from './components/CodeExampleBrowser';
import DataVisualization from './components/DataVisualization';
import ConnectionTest from './components/ConnectionTest';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'search':
        return <SearchInterface />;
      case 'documents':
        return <DocumentExplorer />;
      case 'sources':
        return <SourceManagement />;
      case 'code':
        return <CodeExampleBrowser />;
      case 'visualization':
        return <DataVisualization />;
      case 'connection':
        return <ConnectionTest />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Crawl4AI MCP Visualizer</h1>
        <p>
          Visualize crawled websites, embedding descriptions, and other useful information
        </p>
      </header>
      <Navigation activeTab={activeTab} onTabChange={setActiveTab} />
      <main>
        {renderActiveTab()}
      </main>
    </div>
  );
}

export default App;