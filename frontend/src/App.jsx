import React, { useState, useEffect, useCallback } from 'react';
import { api } from './services/api';
import { Navbar } from './components/Navbar';
import { SearchBar } from './components/SearchBar';
import { SearchResultCard } from './components/SearchResultCard';
import { Pagination } from './components/Pagination';
import { DocumentModal } from './components/DocumentModal';
import { AdminDashboard } from './components/AdminDashboard';
import './index.css';

export function App() {
  const [activeTab, setActiveTab] = useState('search');
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

  // Trigger re-search if algo or mode changes when a query is already active
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

  const queryTerms = query ? query.toLowerCase().split(/\s+/).filter(Boolean) : [];

  return (
    <div className="app-layout">
      <Navbar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        health={health}
      />

      <main className="main-content">
        {activeTab === 'admin' ? (
          <AdminDashboard onSourceAdded={checkHealth} />
        ) : (
          <div className="search-page-container">
            {/* Search Header / Hero */}
            <div className={`search-hero ${searchResponse ? 'has-results' : ''}`}>
              {!searchResponse && (
                <div className="hero-branding">
                  <h1 className="hero-title">
                    Search<span className="brand-accent">X</span>
                  </h1>
                  <p className="hero-subtitle">
                    High-performance document search engine powered by custom C++ retrieval core.
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
              />
            </div>

            {/* Error State */}
            {error && (
              <div className="search-error-banner" role="alert">
                <span className="error-icon">⚠️</span>
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

            {/* Initial / Empty State Before Query */}
            {!loading && !searchResponse && !error && (
              <div className="empty-prompt-card">
                <h2>Explore the Ingested Corpus</h2>
                <p>Try searching for core information-retrieval concepts or indexed topics:</p>
                <div className="sample-queries">
                  {['inverted index', 'bm25', 'tf-idf', 'retrieval', 'normalization'].map((term) => (
                    <button
                      key={term}
                      type="button"
                      className="sample-query-pill"
                      onClick={() => executeSearch(term, 1)}
                    >
                      🔍 {term}
                    </button>
                  ))}
                </div>
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
                  <span>
                    About <strong>{searchResponse.total_hits}</strong> results for{' '}
                    <em>"{searchResponse.query}"</em> (Algorithm:{' '}
                    <strong className="algo-tag">{searchResponse.algorithm.toUpperCase()}</strong>, Match:{' '}
                    <strong>{mode.toUpperCase()}</strong>)
                  </span>
                </div>

                {/* Zero Results Handling */}
                {searchResponse.total_hits === 0 ? (
                  <div className="zero-results-card">
                    <span className="zero-icon">🔍</span>
                    <h3>No matching documents found</h3>
                    <p>
                      Your search - <strong>{searchResponse.query}</strong> - did not match any documents in the index.
                    </p>
                    <ul className="search-tips">
                      <li>Make sure all words are spelled correctly.</li>
                      <li>Try different or more general keywords.</li>
                      <li>Switch match mode from <strong>Match All (AND)</strong> to <strong>Match Any (OR)</strong>.</li>
                      <li>Add more crawl sources in the Admin Dashboard.</li>
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
