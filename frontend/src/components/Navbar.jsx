import React from 'react';

export function Navbar({ activeTab, onTabChange, health }) {
  return (
    <header className="navbar">
      <div className="nav-container">
        <div className="nav-brand" onClick={() => onTabChange('search')} role="button" tabIndex={0}>
          <span className="brand-logo">🔍</span>
          <span className="brand-name">Search<span className="brand-accent">X</span></span>
        </div>

        <nav className="nav-links">
          <button
            type="button"
            className={`nav-btn ${activeTab === 'search' ? 'active' : ''}`}
            onClick={() => onTabChange('search')}
          >
            Search
          </button>
          <button
            type="button"
            className={`nav-btn ${activeTab === 'admin' ? 'active' : ''}`}
            onClick={() => onTabChange('admin')}
          >
            ⚙️ Admin Dashboard
          </button>
        </nav>

        <div className="nav-status">
          {health ? (
            <span className="status-badge status-online" title={`Index: ${health.index_stats?.total_documents || 0} docs, Vocab: ${health.index_stats?.vocabulary_size || 0} terms`}>
              <span className="status-dot"></span> Core Online ({health.index_stats?.total_documents || 0} docs)
            </span>
          ) : (
            <span className="status-badge status-offline">
              <span className="status-dot"></span> Checking backend...
            </span>
          )}
        </div>
      </div>
    </header>
  );
}
