import React from 'react';

export function Navbar({ activeTab, onTabChange, health, darkMode, onToggleDarkMode }) {
  return (
    <header className="navbar">
      <div className="nav-container">
        {/* Brand Logo with 3D Purple X */}
        <div className="nav-brand" onClick={() => onTabChange('search')} role="button" tabIndex={0}>
          <div className="brand-x-emblem">
            <span className="x-glow">✕</span>
          </div>
          <span className="brand-name">Search<span className="brand-accent">X</span></span>
        </div>

        {/* Center Navigation Pills matching the design */}
        <nav className="nav-links">
          <button
            type="button"
            className={`nav-btn ${activeTab === 'search' ? 'active' : ''}`}
            onClick={() => onTabChange('search')}
          >
            <span className="nav-icon">🏠</span> Home
          </button>
          <button
            type="button"
            className="nav-btn"
            onClick={() => onTabChange('search')}
            title="Explore topics"
          >
            <span className="nav-icon">🧭</span> Explore
          </button>
          <button
            type="button"
            className="nav-btn"
            onClick={() => onTabChange('search')}
            title="Saved Collections"
          >
            <span className="nav-icon">📁</span> Collections
          </button>
          <button
            type="button"
            className={`nav-btn ${activeTab === 'admin' ? 'active' : ''}`}
            onClick={() => onTabChange('admin')}
            title="Analytics & Administration"
          >
            <span className="nav-icon">📊</span> Analytics
          </button>
        </nav>

        {/* Right Actions: Dark/Light Mode & Avatar */}
        <div className="nav-actions">
          {/* Status pill */}
          {health && (
            <span className="status-badge status-online" title={`Index: ${health.index_stats?.total_documents || 0} docs, Vocab: ${health.index_stats?.vocabulary_size || 0} terms`}>
              <span className="status-dot"></span> Core Online ({health.index_stats?.total_documents || 0} docs)
            </span>
          )}

          {/* Theme Toggle Switch */}
          <button
            type="button"
            className="theme-toggle-pill"
            onClick={onToggleDarkMode}
            title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            aria-label="Toggle dark mode"
          >
            <span className={`toggle-icon ${!darkMode ? 'active' : ''}`}>☀️</span>
            <span className={`toggle-icon ${darkMode ? 'active' : ''}`}>🌙</span>
          </button>

          {/* User Avatar Circle */}
          <button
            type="button"
            className="user-avatar-btn"
            onClick={() => onTabChange('admin')}
            title="Admin Profile"
            aria-label="Admin Profile"
          >
            👤
          </button>
        </div>
      </div>
    </header>
  );
}
