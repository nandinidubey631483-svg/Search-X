import React, { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';
import {
  IconSearch,
  IconMic,
  IconCamera,
  IconSliders,
  IconX,
  IconGlobe,
  IconImage,
  IconFileText,
  IconNewspaper,
  IconGraduationCap,
} from './Icons';

export function SearchBar({
  initialQuery = '',
  onSearch,
  loading = false,
  algo = 'bm25',
  setAlgo,
  mode = 'any',
  setMode,
  activeCategory = 'web',
  onSelectCategory,
}) {
  const [query, setQuery] = useState(initialQuery);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [voiceActive, setVoiceActive] = useState(false);
  const debounceRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    setQuery(initialQuery);
  }, [initialQuery]);

  // Handle autocomplete suggestion fetching with debounce
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

  // Simple browser SpeechRecognition support if available
  const handleVoiceSearch = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Voice search is not supported in this browser. Please type your query.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;

    recognition.onstart = () => setVoiceActive(true);
    recognition.onend = () => setVoiceActive(false);
    recognition.onerror = () => setVoiceActive(false);

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setQuery(transcript);
      onSearch(transcript);
    };

    recognition.start();
  };

  const categories = [
    { id: 'web', label: 'Web', icon: <IconGlobe size={15} /> },
    { id: 'images', label: 'Images', icon: <IconImage size={15} /> },
    { id: 'documents', label: 'Documents', icon: <IconFileText size={15} /> },
    { id: 'news', label: 'News', icon: <IconNewspaper size={15} /> },
    { id: 'scholar', label: 'Scholar', icon: <IconGraduationCap size={15} /> },
  ];

  return (
    <div className="search-bar-container" ref={containerRef}>
      <form onSubmit={handleSubmit} className="search-form" role="search">
        <div className="input-wrapper">
          <span className="search-icon-left">
            <IconSearch size={20} />
          </span>

          <input
            type="text"
            className="search-input"
            placeholder={
              activeCategory === 'images'
                ? 'Search images, diagrams & architecture visuals...'
                : activeCategory === 'documents'
                ? 'Search technical documentation, whitepapers & tutorials...'
                : activeCategory === 'news'
                ? 'Search engineering changelogs, blogs & crawl news...'
                : activeCategory === 'scholar'
                ? 'Search academic research, IR papers & benchmarks...'
                : 'Search the web with SearchX...'
            }
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setShowSuggestions(true);
            }}
            onFocus={() => setShowSuggestions(true)}
            autoComplete="off"
            aria-label="Search the web with SearchX"
          />

          {query && (
            <button
              type="button"
              className="action-icon-btn clear-btn"
              onClick={() => {
                setQuery('');
                setSuggestions([]);
              }}
              title="Clear input"
              aria-label="Clear input"
            >
              <IconX size={16} />
            </button>
          )}

          {/* Voice Search Button */}
          <button
            type="button"
            className={`action-icon-btn ${voiceActive ? 'voice-pulse' : ''}`}
            onClick={handleVoiceSearch}
            title={voiceActive ? 'Listening...' : 'Voice Search'}
            aria-label="Voice Search"
          >
            <IconMic size={18} />
          </button>

          {/* Visual / Document Search Lens Button */}
          <button
            type="button"
            className="action-icon-btn"
            onClick={() => alert("Document and Visual Search: Select document from below or drag & drop text/JSON files into Admin Dashboard.")}
            title="Visual / Document Lens"
            aria-label="Document Lens"
          >
            <IconCamera size={18} />
          </button>

          {/* Settings / Filters Toggle */}
          <button
            type="button"
            className={`action-icon-btn filter-btn ${showFilters ? 'active' : ''}`}
            onClick={() => setShowFilters(!showFilters)}
            title="Algorithm & Retrieval Filters"
            aria-label="Retrieval Filters"
          >
            <IconSliders size={18} />
          </button>

          {/* Gradient Circular Submit Button matching the screenshot */}
          <button
            type="submit"
            className="search-submit-circle"
            disabled={loading || !query.trim()}
            title="Search"
            aria-label="Search"
          >
            {loading ? <span className="spinner-white"></span> : <IconSearch size={18} />}
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
                <span className="suggestion-icon">
                  <IconSearch size={14} />
                </span>
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
            <label className="filter-label" htmlFor="mode-select">Match Mode:</label>
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

      {/* Category Tabs matching the screenshot (Web, Images, Documents, News, Scholar) */}
      <div className="category-tabs-container">
        {categories.map((cat) => (
          <button
            key={cat.id}
            type="button"
            className={`category-pill ${activeCategory === cat.id ? 'active' : ''}`}
            onClick={() => onSelectCategory && onSelectCategory(cat.id)}
          >
            <span className="category-icon">{cat.icon}</span>
            <span className="category-label">{cat.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
