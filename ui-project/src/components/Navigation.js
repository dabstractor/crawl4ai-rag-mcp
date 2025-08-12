import React, { useMemo, useState } from 'react';
import './Navigation.css';
import { Theme, getStoredTheme, storeTheme, applyTheme } from '../utils/theme';

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

  const [theme, setTheme] = useState(() => getStoredTheme());

  const handleThemeChange = (next) => {
    setTheme(next);
    storeTheme(next);
    applyTheme(next);
  };

  const themeLabel = useMemo(() => {
    switch (theme) {
      case Theme.Light:
        return 'Light';
      case Theme.Dark:
        return 'Dark';
      default:
        return 'System';
    }
  }, [theme]);

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
        <li className="nav-item nav-theme">
          <div className="theme-switcher">
            <label className="theme-label" aria-label="Theme selector">{themeLabel}</label>
            <div className="theme-buttons" role="group" aria-label="Theme selector">
              <button className={`theme-btn ${theme === Theme.Light ? 'active' : ''}`} onClick={() => handleThemeChange(Theme.Light)} title="Light">🌞</button>
              <button className={`theme-btn ${theme === Theme.System ? 'active' : ''}`} onClick={() => handleThemeChange(Theme.System)} title="System">🖥️</button>
              <button className={`theme-btn ${theme === Theme.Dark ? 'active' : ''}`} onClick={() => handleThemeChange(Theme.Dark)} title="Dark">🌙</button>
            </div>
          </div>
        </li>
      </ul>
    </nav>
  );
};

export default Navigation;