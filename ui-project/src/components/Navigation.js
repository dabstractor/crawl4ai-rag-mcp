import React, { useState } from 'react';
import './Navigation.css';

const Navigation = ({ activeTab, onTabChange }) => {
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'search', label: 'Search', icon: '🔍' },
    { id: 'documents', label: 'Documents', icon: '📄' },
    { id: 'sources', label: 'Sources', icon: '🌐' },
    { id: 'code', label: 'Code Examples', icon: '💻' },
    { id: 'visualization', label: 'Visualization', icon: '📈' },
    { id: 'connection', label: 'Connection', icon: '🔌' }
  ];

  return (
    <nav className="navigation">
      <ul className="nav-tabs">
        {tabs.map((tab) => (
          <li key={tab.id} className="nav-item">
            <button
              className={`nav-link ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => onTabChange(tab.id)}
            >
              <span className="nav-icon">{tab.icon}</span>
              <span className="nav-label">{tab.label}</span>
            </button>
          </li>
        ))}
      </ul>
    </nav>
  );
};

export default Navigation;