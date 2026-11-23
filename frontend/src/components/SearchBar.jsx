import React, { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';

export function SearchBar({
  initialQuery = '',
  onSearch,
  loading = false,
  algo = 'bm25',
  setAlgo,
  mode = 'any',
  setMode,
}) {
  const [query, setQuery] = useState(initialQuery);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const debounceRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    setQuery(initialQuery);
  }, [initialQuery]);

  // Handle autocomplete suggestion fetching with 200ms debounce
  useEffect(() => {
    if (!query.trim() || query.length < 2) {
      setSuggestions([]);
      return;
    }

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(async () => {
      try {
        const terms = await api.getSuggestions(query, 5);
        setSuggestions(terms);
      } catch {
        setSuggestions([]);
      }
    }, 200);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query]);

  // Close suggestions when clicking outside
  useEffect(() => {
    function handleClickOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setShowSuggestions(false);
    onSearch(query.trim());
  };

  const handleSelectSuggestion = (suggestion) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    onSearch(suggestion);
  };

  return (
    <div className="search-bar-container" ref={containerRef}>
      <form onSubmit={handleSubmit} className="search-form" role="search">
        <div className="input-wrapper">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            className="search-input"
            placeholder="Search documents, topics, or terms..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setShowSuggestions(true);
            }}
            onFocus={() => setShowSuggestions(true)}
            autoComplete="off"
            aria-label="Search documents"
          />

          {query && (
            <button
              type="button"
              className="clear-btn"
              onClick={() => {
                setQuery('');
                setSuggestions([]);
              }}
              title="Clear input"
            >
              ✕
            </button>
          )}

          <button
            type="button"
            className={`filter-toggle-btn ${showFilters ? 'active' : ''}`}
            onClick={() => setShowFilters(!showFilters)}
            title="Toggle retrieval algorithm and match mode"
          >
            ⚙️ Filters
          </button>

          <button type="submit" className="submit-btn" disabled={loading || !query.trim()}>
            {loading ? <span className="spinner"></span> : 'Search'}
          </button>
        </div>

        {/* Autocomplete Suggestions Dropdown */}
        {showSuggestions && suggestions.length > 0 && (
          <ul className="suggestions-list" role="listbox">
            {suggestions.map((item, idx) => (
              <li
                key={idx}
                className="suggestion-item"
                onClick={() => handleSelectSuggestion(item)}
                role="option"
                aria-selected="false"
              >
                <span className="suggestion-icon">🔎</span>
                <span className="suggestion-text">{item}</span>
              </li>
            ))}
          </ul>
        )}
      </form>

      {/* Collapsible Search Filters */}
      {showFilters && (
        <div className="search-filters-panel">
          <div className="filter-group">
            <label className="filter-label" htmlFor="algo-select">Ranking Algorithm:</label>
            <select
              id="algo-select"
              className="filter-select"
              value={algo}
              onChange={(e) => setAlgo(e.target.value)}
            >
              <option value="bm25">Okapi BM25 (Default)</option>
              <option value="tf_idf">TF-IDF (Sublinear)</option>
            </select>
          </div>

          <div className="filter-group">
            <label className="filter-label" htmlFor="mode-select">Query Match Mode:</label>
            <select
              id="mode-select"
              className="filter-select"
              value={mode}
              onChange={(e) => setMode(e.target.value)}
            >
              <option value="any">Match Any Term (OR)</option>
              <option value="all">Match All Terms (AND)</option>
            </select>
          </div>
        </div>
      )}
    </div>
  );
}
