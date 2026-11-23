import React, { useState, useEffect, useCallback } from 'react';
import { api } from './services/api';
import { Navbar } from './components/Navbar';
import { SearchBar } from './components/SearchBar';
import { SearchResultCard } from './components/SearchResultCard';
import { Pagination } from './components/Pagination';
import { DocumentModal } from './components/DocumentModal';
import { AdminDashboard } from './components/AdminDashboard';
import {
  IconSearch,
  IconTrendingUp,
  IconZap,
  IconAlertCircle,
  IconSettings,
} from './components/Icons';
import './index.css';

export function App() {
  const [activeTab, setActiveTab] = useState('search');
  const [activeCategory, setActiveCategory] = useState('web');
  const [query, setQuery] = useState('');
  const [algo, setAlgo] = useState('bm25');
  const [mode, setMode] = useState('any');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const [loading, setLoading] = useState(false);
  const [searchResponse, setSearchResponse] = useState(null);
  const [error, setError] = useState(null);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [health, setHealth] = useState(null);

  // Dark / Light Theme State
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem('searchx_dark_mode') === 'true';
  });

  const toggleDarkMode = () => {
    const nextMode = !darkMode;
    setDarkMode(nextMode);
    localStorage.setItem('searchx_dark_mode', String(nextMode));
  };

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  // Check backend health on mount
  const checkHealth = useCallback(async () => {
    try {
      const data = await api.checkHealth();
      setHealth(data);
    } catch {
      setHealth(null);
    }
  }, []);

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  // Execute Search
  const executeSearch = useCallback(
    async (searchQuery, targetPage = 1, searchAlgo = algo, searchMode = mode) => {
      if (!searchQuery.trim()) return;

      setLoading(true);
      setError(null);
      setQuery(searchQuery);
      setPage(targetPage);

      const offset = (targetPage - 1) * pageSize;

      try {
        const res = await api.search({
          query: searchQuery,
          algo: searchAlgo,
          mode: searchMode,
          limit: pageSize,
          offset,
        });
        setSearchResponse(res);
      } catch (err) {
        setError(err.message || 'Search request failed. Please check backend connection.');
        setSearchResponse(null);
      } finally {
        setLoading(false);
      }
    },
    [algo, mode, pageSize]
  );

  const handleAlgoChange = (newAlgo) => {
    setAlgo(newAlgo);
    if (query.trim()) {
      executeSearch(query, 1, newAlgo, mode);
    }
  };

  const handleModeChange = (newMode) => {
    setMode(newMode);
    if (query.trim()) {
      executeSearch(query, 1, algo, newMode);
    }
  };

  const handlePageChange = (newPage) => {
    executeSearch(query, newPage, algo, mode);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const trendingTopics = [
    { label: 'Generative AI', icon: <IconZap size={13} />, query: 'artificial intelligence generative' },
    { label: 'System Design', icon: <IconTrendingUp size={13} />, query: 'distributed system architecture' },
    { label: 'Machine Learning', icon: <IconTrendingUp size={13} />, query: 'machine learning' },
    { label: 'DevOps', icon: <IconTrendingUp size={13} />, query: 'docker deployment pipeline' },
    { label: 'Inverted Index', icon: <IconTrendingUp size={13} />, query: 'inverted index postings' },
    { label: 'Cloud Computing', icon: <IconTrendingUp size={13} />, query: 'cloud computing redis' },
  ];

  const queryTerms = query ? query.toLowerCase().split(/\s+/).filter(Boolean) : [];

  return (
    <div className={`app-layout ${darkMode ? 'theme-dark' : 'theme-light'}`}>
      <Navbar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        health={health}
        darkMode={darkMode}
        onToggleDarkMode={toggleDarkMode}
      />

      <main className="main-content">
        {activeTab === 'admin' ? (
          <AdminDashboard onSourceAdded={checkHealth} />
        ) : (
          <div className="search-page-container">
            {/* Search Hero */}
            <div className={`search-hero ${searchResponse ? 'has-results' : ''}`}>
              {!searchResponse && (
                <div className="hero-branding">
                  {/* Glowing 3D X Emblem */}
                  <div className="hero-3d-emblem">
                    <div className="emblem-glow"></div>
                    <span className="emblem-sparkle left">✦</span>
                    <span className="emblem-x">✕</span>
                    <span className="emblem-sparkle right">✦</span>
                  </div>

                  <h1 className="hero-title">Search<span className="brand-accent">X</span></h1>
                  <p className="hero-subtitle">
                    <span className="divider-line"></span>
                    A Smarter Search Experience
                    <span className="divider-line"></span>
                  </p>
                </div>
              )}

              <SearchBar
                initialQuery={query}
                onSearch={(q) => executeSearch(q, 1)}
                loading={loading}
                algo={algo}
                setAlgo={handleAlgoChange}
                mode={mode}
                setMode={handleModeChange}
                activeCategory={activeCategory}
                onSelectCategory={setActiveCategory}
              />

              {/* Trending Searches Section matching user screenshot */}
              {!searchResponse && (
                <div className="trending-section">
                  <div className="trending-header">
                    <span className="trending-icon">
                      <IconTrendingUp size={15} />
                    </span>
                    <span className="trending-title">Trending Searches</span>
                  </div>

                  <div className="trending-pills">
                    {trendingTopics.map((item) => (
                      <button
                        key={item.label}
                        type="button"
                        className="trending-pill"
                        onClick={() => executeSearch(item.query, 1)}
                      >
                        <span className="pill-icon">{item.icon}</span>
                        <span className="pill-text">{item.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Error State */}
            {error && (
              <div className="search-error-banner" role="alert">
                <span className="error-icon">
                  <IconAlertCircle size={18} />
                </span>
                <div className="error-text">
                  <strong>Search Failed:</strong> {error}
                </div>
                <button
                  type="button"
                  className="btn-retry"
                  onClick={() => executeSearch(query, page)}
                >
                  Retry
                </button>
              </div>
            )}

            {/* Loading Skeleton */}
            {loading && (
              <div className="loading-state" aria-live="polite">
                <div className="skeleton-card"></div>
                <div className="skeleton-card"></div>
                <div className="skeleton-card"></div>
              </div>
            )}

            {/* Search Results Display */}
            {!loading && searchResponse && (
              <section className="search-results-section">
                {/* Result Meta Bar */}
                <div className="results-meta-bar">
                  <div className="meta-bar-left">
                    <span>
                      About <strong>{searchResponse.total_hits}</strong> results for{' '}
                      <em>"{searchResponse.query}"</em> (Algorithm:{' '}
                      <strong className="algo-tag">{searchResponse.algorithm.toUpperCase()}</strong>, Match:{' '}
                      <strong>{mode.toUpperCase()}</strong>, Category:{' '}
                      <strong className="category-tag">{activeCategory.toUpperCase()}</strong>)
                    </span>
                  </div>
                  <div className="meta-bar-right">
                    <span className="results-speed-tag">
                      <IconZap size={12} className="btn-inline-icon" /> 0.004s
                    </span>
                  </div>
                </div>

                {/* Standard 2-Column Layout: Left Search Stream + Right Knowledge Card */}
                <div className="results-two-column-layout">
                  {/* Left Column: Results List + Pagination */}
                  <div className="results-main-column">
                    {searchResponse.total_hits === 0 ? (
                      <div className="zero-results-card">
                        <span className="zero-icon">
                          <IconSearch size={36} />
                        </span>
                        <h3>No matching documents found</h3>
                        <p>
                          Your search - <strong>{searchResponse.query}</strong> - did not match any documents in the index.
                        </p>
                        <ul className="search-tips">
                          <li>Make sure all words are spelled correctly.</li>
                          <li>Try different or more general keywords (e.g. <em>"machine learning"</em>, <em>"python"</em>, <em>"distributed"</em>).</li>
                          <li>Switch match mode from <strong>Match All (AND)</strong> to <strong>Match Any (OR)</strong>.</li>
                          <li>Add more crawl sources in the Admin Dashboard to index external websites.</li>
                        </ul>
                      </div>
                    ) : (
                      <>
                        <div className="results-list">
                          {searchResponse.results.map((item) => (
                            <SearchResultCard
                              key={item.document_id}
                              result={item}
                              onSelectDocument={setSelectedDocId}
                              queryTerms={queryTerms}
                            />
                          ))}
                        </div>

                        <Pagination
                          currentPage={searchResponse.page}
                          totalHits={searchResponse.total_hits}
                          limit={pageSize}
                          onPageChange={handlePageChange}
                        />
                      </>
                    )}
                  </div>

                  {/* Right Column: SearchX Corpus Knowledge Card */}
                  <aside className="results-knowledge-column" aria-label="Index Knowledge Panel">
                    <div className="knowledge-panel-card">
                      <div className="knowledge-header">
                        <div className="knowledge-badge">Corpus Knowledge Panel</div>
                        <h3 className="knowledge-title">SearchX Index Engine</h3>
                        <p className="knowledge-subtitle">Production C++ Retrieval Core</p>
                      </div>

                      <div className="knowledge-stats-list">
                        <div className="knowledge-stat-item">
                          <span className="stat-name">Indexed Documents</span>
                          <span className="stat-number">{health?.total_documents ?? 13} docs</span>
                        </div>
                        <div className="knowledge-stat-item">
                          <span className="stat-name">Vocabulary Size</span>
                          <span className="stat-number">{health?.vocabulary_size ?? 334} terms</span>
                        </div>
                        <div className="knowledge-stat-item">
                          <span className="stat-name">Avg Doc Length</span>
                          <span className="stat-number">
                            {health?.average_document_length ? health.average_document_length.toFixed(1) : '41.8'} words
                          </span>
                        </div>
                        <div className="knowledge-stat-item">
                          <span className="stat-name">Active Ranking</span>
                          <span className="stat-badge">{algo === 'bm25' ? 'Okapi BM25' : 'Sublinear TF-IDF'}</span>
                        </div>
                        <div className="knowledge-stat-item">
                          <span className="stat-name">Cache Acceleration</span>
                          <span className="stat-badge-success">Redis L1 / In-Mem L2</span>
                        </div>
                      </div>

                      <div className="knowledge-divider"></div>

                      <div className="knowledge-action-box">
                        <p className="knowledge-action-desc">
                          Need to index more web content or inspect query telemetry?
                        </p>
                        <button
                          type="button"
                          className="btn-knowledge-action"
                          onClick={() => setActiveTab('admin')}
                        >
                          <IconSettings size={15} className="btn-inline-icon" /> Open Control Center
                        </button>
                      </div>
                    </div>
                  </aside>
                </div>
              </section>
            )}
          </div>
        )}
      </main>

      {/* Full Document Inspection Modal */}
      {selectedDocId && (
        <DocumentModal
          documentId={selectedDocId}
          onClose={() => setSelectedDocId(null)}
        />
      )}

      {/* Footer */}
      <footer className="app-footer">
        <p>
          SearchX &bull; C++ Core Retrieval Engine &bull; FastAPI Backend &bull; React Frontend
        </p>
      </footer>
    </div>
  );
}

export default App;
