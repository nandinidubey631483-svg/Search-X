import React from 'react';
import { IconSettings } from './Icons';

export function Navbar({ activeTab, onTabChange, health, darkMode, onToggleDarkMode }) {
  return (
    <header className="navbar">
      <div className="nav-container">
        {/* Left: Brand Logo */}
        <div
          className="nav-brand"
          onClick={() => onTabChange('search')}
          role="button"
          tabIndex={0}
          aria-label="SearchX Home"
        >
          <div className="brand-icon-box">
            <svg
              className="brand-svg-logo"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="11" cy="11" r="7" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
              <path d="m8 8 6 6" />
              <path d="m14 8-6 6" />
            </svg>
          </div>
          <div className="brand-text-group">
            <span className="brand-name">
              Search<span className="brand-accent">X</span>
            </span>
            <span className="brand-engine-tag">Core v1.0</span>
          </div>
        </div>

        {/* Center: Navigation Tabs */}
        <nav className="nav-links" aria-label="Main Navigation">
          <button
            type="button"
            className={`nav-tab-item ${activeTab === 'search' ? 'active' : ''}`}
            onClick={() => onTabChange('search')}
          >
            <svg className="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <span>Search</span>
          </button>
          <button
            type="button"
            className={`nav-tab-item ${activeTab === 'admin' ? 'active' : ''}`}
            onClick={() => onTabChange('admin')}
          >
            <svg className="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
              <line x1="8" y1="21" x2="16" y2="21" />
              <line x1="12" y1="17" x2="12" y2="21" />
            </svg>
            <span>Admin Dashboard</span>
          </button>
        </nav>

        {/* Right: Actions & Core Status */}
        <div className="nav-actions">
          {health && (
            <div
              className="core-status-pill"
              title={`Inverted Index: ${health.index_stats?.total_documents || 0} documents, ${health.index_stats?.vocabulary_size || 0} unique terms`}
            >
              <span className="status-dot"></span>
              <span className="status-text">
                Core Online ({health.index_stats?.total_documents || 0} docs)
              </span>
            </div>
          )}

          {/* Theme Toggle Button */}
          <button
            type="button"
            className="theme-toggle-btn"
            onClick={onToggleDarkMode}
            title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            aria-label="Toggle theme"
          >
            {darkMode ? (
              <svg className="theme-svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="5" />
                <line x1="12" y1="1" x2="12" y2="3" />
                <line x1="12" y1="21" x2="12" y2="23" />
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                <line x1="1" y1="12" x2="3" y2="12" />
                <line x1="21" y1="12" x2="23" y2="12" />
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
              </svg>
            ) : (
              <svg className="theme-svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
            )}
          </button>

          {/* Control Center Pill / Quick Launch */}
          <button
            type="button"
            className={`admin-shortcut-btn ${activeTab === 'admin' ? 'active' : ''}`}
            onClick={() => onTabChange('admin')}
            title="Open SearchX Admin Control Center"
          >
            <IconSettings size={15} />
            <span className="shortcut-text">Control Center</span>
          </button>
        </div>
      </div>
    </header>
  );
}
