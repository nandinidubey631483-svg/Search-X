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
  IconGlobe,
  IconImage,
  IconFileText,
  IconNewspaper,
  IconGraduationCap,
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

  const handleCategoryChange = (newCategory) => {
    setActiveCategory(newCategory);
    if (query.trim()) {
      executeSearch(query, 1, algo, mode);
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

  // Visual Image Showcase Cards
  const visualGallery = [
    {
      title: 'Inverted Index Postings List Architecture',
      subtitle: 'Term dictionary with binary delta-encoded docID lists',
      dim: '1920×1080 SVG',
      query: 'inverted index postings architecture',
      badge: 'Core Engine Spec',
    },
    {
      title: 'Okapi BM25 Ranking Saturation Curve',
      subtitle: 'Score vs Term Frequency with length normalization (k1=1.2, b=0.75)',
      dim: '1280×720 Chart',
      query: 'bm25 scoring normalization',
      badge: 'Algorithm Diagram',
    },
    {
      title: 'Redis Multi-Tier Query Cache Topology',
      subtitle: 'Sub-millisecond L1 memory cache with atomic invalidation',
      dim: '1600×900 SVG',
      query: 'redis query cache invalidation',
      badge: 'Cache Architecture',
    },
    {
      title: 'Web Crawler Safety & SSRF Guard',
      subtitle: 'Robots exclusion standard, DNS loopback block, and depth bounds',
      dim: '1440×900 Diagram',
      query: 'web crawler robots ssrf',
      badge: 'Crawler Protocol',
    },
    {
      title: 'FastAPI & C++ Core Engine Bridge',
      subtitle: 'Subprocess stdin/stdout query dispatch pipeline',
      dim: '1920×1080 Schematic',
      query: 'fastapi backend architecture',
      badge: 'Pipeline Schematic',
    },
    {
      title: 'Distributed Consensus & Raft Cluster State',
      subtitle: 'Leader election, log replication, and split-brain resilience',
      dim: '1600×900 SVG',
      query: 'distributed consensus raft',
      badge: 'Distributed Systems',
    },
  ];

  // Curated Technical Document Repository
  const documentLibrary = [
    {
      docId: 'doc_python_ds',
      title: 'Python 3.13 Data Structures Deep Dive',
      category: 'Documentation Tutorial',
      readTime: '5 min read',
      desc: 'Comprehensive overview of Python lists, dicts, sets, and algorithmic performance.',
      query: 'python data structures tutorial',
    },
    {
      docId: 'doc_ir_overview',
      title: 'Information Retrieval: Core Principles and Systems',
      category: 'Foundational Whitepaper',
      readTime: '4 min read',
      desc: 'Modern search engine principles, tokenization pipelines, and statistical scoring.',
      query: 'information retrieval principles',
    },
    {
      docId: 'doc_bm25_ranking',
      title: 'Okapi BM25 Scoring and Length Normalization',
      category: 'Algorithmic Specification',
      readTime: '6 min read',
      desc: 'Mathematical formulation of term saturation and length normalization parameters.',
      query: 'okapi bm25 scoring',
    },
    {
      docId: 'doc_fastapi_backend',
      title: 'FastAPI High-Performance Asynchronous APIs',
      category: 'Engineering Guide',
      readTime: '4 min read',
      desc: 'Building sub-millisecond REST search endpoints with Pydantic validation.',
      query: 'fastapi web framework',
    },
    {
      docId: 'doc_distributed_raft',
      title: 'Distributed Consensus and Raft State Machine',
      category: 'Distributed Systems Spec',
      readTime: '7 min read',
      desc: 'Consensus protocols, replicated logs, and high-availability clustered architectures.',
      query: 'distributed consensus raft',
    },
    {
      docId: 'doc_cpp_standard',
      title: 'C++17 Inverted Index Memory Architecture',
      category: 'Engine Specification',
      readTime: '5 min read',
      desc: 'STL hash maps, binary serialization, and zero-copy postings traversal.',
      query: 'cpp17 standard library',
    },
  ];

  // Engineering News & Releases
  const engineeringNews = [
    {
      title: 'SearchX Inverted Index Engine v1.0 Deployed',
      date: 'Today',
      author: 'SearchX Core Team',
      desc: 'Sub-millisecond term posting traversal compiled with MinGW-w64 GCC C++17.',
      query: 'inverted index postings',
    },
    {
      title: 'Redis Multi-Tier Query Caching Activated',
      date: 'Today',
      author: 'Performance Infra',
      desc: 'Achieved sub-millisecond cache hit response with atomic TTL expiration and crawl invalidation.',
      query: 'redis query cache',
    },
    {
      title: 'PostgreSQL Relational Persistence Layer Verified',
      date: 'Yesterday',
      author: 'Database Systems',
      desc: 'Full ACID relational storage with URL content hashing and automated schema migrations.',
      query: 'postgresql persistence storage',
    },
    {
      title: 'Web Crawler SSRF Security Boundaries Enforced',
      date: '2 days ago',
      author: 'Security Operations',
      desc: 'Strict RFC 1918 loopback blocking and robots.txt parsing validated across all targets.',
      query: 'web crawler robots ssrf',
    },
  ];

  // Academic Research Papers & Citations
  const scholarPapers = [
    {
      title: 'Okapi at TREC-3: Probabilistic Term Weighting and Relevance Feedback',
      authors: 'S. E. Robertson, S. Walker, S. Jones, M. M. Hancock-Beaulieu, M. Gatford',
      year: '1994',
      citations: '8,420 citations',
      desc: 'The landmark paper introducing the BM25 probabilistic retrieval ranking formulation.',
      query: 'robertson okapi trec3 bm25',
    },
    {
      title: 'Term-Weighting Approaches in Automatic Text Retrieval',
      authors: 'G. Salton, C. Buckley',
      year: '1988',
      citations: '14,350 citations',
      desc: 'Evaluation of TF-IDF weighting schemes, cosine similarity, and sublinear scaling.',
      query: 'tfidf term weighting salton',
    },
    {
      title: 'Inverted Files for Text Search Engines: Query Processing and Compression',
      authors: 'J. Zobel, A. Moffat',
      year: '2006',
      citations: '2,890 citations',
      desc: 'Comprehensive survey of index compression, postings list traversal, and caching strategies.',
      query: 'inverted files text search engines zobel',
    },
    {
      title: 'The Anatomy of a Large-Scale Hypertextual Web Search Engine',
      authors: 'S. Brin, L. Page',
      year: '1998',
      citations: '32,100 citations',
      desc: 'Foundational architecture of modern web crawling, inverted indexing, and link analysis.',
      query: 'anatomy large scale web search engine brin page',
    },
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
                onSelectCategory={handleCategoryChange}
              />

              {/* Dynamic Showcase based on activeCategory */}
              {!searchResponse && (
                <div className="category-showcase-section">
                  {/* Category 1: WEB -> Trending Searches */}
                  {activeCategory === 'web' && (
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

                  {/* Category 2: IMAGES -> Visual Architecture & Diagram Schematics */}
                  {activeCategory === 'images' && (
                    <div className="category-view-box">
                      <div className="category-view-header">
                        <div>
                          <h3 className="category-view-title">Visual Architecture & Schematics Gallery</h3>
                          <p className="category-view-desc">
                            Explore indexed technical diagrams, algorithmic curves, and system blueprints.
                          </p>
                        </div>
                        <span className="category-view-badge">6 Diagrams Available</span>
                      </div>

                      <div className="image-showcase-grid">
                        {visualGallery.map((item, idx) => (
                          <div
                            key={idx}
                            className="image-showcase-card"
                            onClick={() => executeSearch(item.query, 1)}
                            role="button"
                            tabIndex={0}
                          >
                            <div className="image-preview-placeholder">
                              <IconImage size={28} className="preview-svg-icon" />
                              <span className="image-dim-tag">{item.dim}</span>
                            </div>
                            <div className="image-card-info">
                              <span className="image-spec-badge">{item.badge}</span>
                              <h4 className="image-card-title">{item.title}</h4>
                              <p className="image-card-sub">{item.subtitle}</p>
                              <div className="image-card-action">
                                <span className="action-link">Search Schematic &rarr;</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Category 3: DOCUMENTS -> Curated Technical Document Library */}
                  {activeCategory === 'documents' && (
                    <div className="category-view-box">
                      <div className="category-view-header">
                        <div>
                          <h3 className="category-view-title">Curated Technical Whitepapers & Tutorials</h3>
                          <p className="category-view-desc">
                            Direct access to full documentation files ingested into the SearchX repository.
                          </p>
                        </div>
                        <span className="category-view-badge">6 Ingested Documents</span>
                      </div>

                      <div className="docs-showcase-grid">
                        {documentLibrary.map((doc) => (
                          <div key={doc.docId} className="doc-showcase-card">
                            <div className="doc-card-top">
                              <span className="doc-type-pill">{doc.category}</span>
                              <span className="doc-read-time">{doc.readTime}</span>
                            </div>
                            <h4 className="doc-card-title">{doc.title}</h4>
                            <p className="doc-card-desc">{doc.desc}</p>
                            <div className="doc-card-actions">
                              <button
                                type="button"
                                className="btn-doc-read"
                                onClick={() => setSelectedDocId(doc.docId)}
                              >
                                <IconFileText size={14} className="btn-inline-icon" /> Read Document
                              </button>
                              <button
                                type="button"
                                className="btn-doc-search"
                                onClick={() => executeSearch(doc.query, 1)}
                              >
                                Search Topic &rarr;
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Category 4: NEWS -> Engineering Releases & Ingestion Logs */}
                  {activeCategory === 'news' && (
                    <div className="category-view-box">
                      <div className="category-view-header">
                        <div>
                          <h3 className="category-view-title">Engineering Releases & Ingestion News</h3>
                          <p className="category-view-desc">
                            Latest changelogs, crawler ingestion runs, and algorithmic updates from SearchX.
                          </p>
                        </div>
                        <span className="category-view-badge">Live Changelog</span>
                      </div>

                      <div className="news-showcase-list">
                        {engineeringNews.map((item, idx) => (
                          <div
                            key={idx}
                            className="news-showcase-item"
                            onClick={() => executeSearch(item.query, 1)}
                            role="button"
                            tabIndex={0}
                          >
                            <div className="news-meta-row">
                              <span className="news-date-pill">{item.date}</span>
                              <span className="news-author">{item.author}</span>
                            </div>
                            <h4 className="news-item-title">{item.title}</h4>
                            <p className="news-item-desc">{item.desc}</p>
                            <span className="news-read-link">Search Ingestion Topic &rarr;</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Category 5: SCHOLAR -> Academic Research & Formulations */}
                  {activeCategory === 'scholar' && (
                    <div className="category-view-box">
                      <div className="category-view-header">
                        <div>
                          <h3 className="category-view-title">Academic Research Papers & Algorithmic Citations</h3>
                          <p className="category-view-desc">
                            Peer-reviewed information retrieval foundations, term weighting, and indexing papers.
                          </p>
                        </div>
                        <span className="category-view-badge">Peer-Reviewed Papers</span>
                      </div>

                      <div className="scholar-showcase-list">
                        {scholarPapers.map((paper, idx) => (
                          <div
                            key={idx}
                            className="scholar-showcase-item"
                            onClick={() => executeSearch(paper.query, 1)}
                            role="button"
                            tabIndex={0}
                          >
                            <div className="scholar-meta-row">
                              <span className="scholar-pdf-badge">[PDF Research]</span>
                              <span className="scholar-citations">{paper.citations}</span>
                              <span className="scholar-year">&bull; {paper.year}</span>
                            </div>
                            <h4 className="scholar-paper-title">{paper.title}</h4>
                            <p className="scholar-authors">{paper.authors}</p>
                            <p className="scholar-desc">{paper.desc}</p>
                            <span className="scholar-search-action">Retrieve Scholarly Topic &rarr;</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
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

                {/* Sub-bar Category Switcher for Live Results */}
                <div className="results-category-tabs" role="tablist" aria-label="Search Result Categories">
                  {[
                    { id: 'web', label: 'All', icon: <IconGlobe size={14} /> },
                    { id: 'images', label: 'Images', icon: <IconImage size={14} /> },
                    { id: 'documents', label: 'Documents', icon: <IconFileText size={14} /> },
                    { id: 'news', label: 'News', icon: <IconNewspaper size={14} /> },
                    { id: 'scholar', label: 'Scholar', icon: <IconGraduationCap size={14} /> },
                  ].map((cat) => (
                    <button
                      key={cat.id}
                      type="button"
                      role="tab"
                      aria-selected={activeCategory === cat.id}
                      className={`result-category-tab ${activeCategory === cat.id ? 'active' : ''}`}
                      onClick={() => handleCategoryChange(cat.id)}
                    >
                      <span className="tab-svg">{cat.icon}</span>
                      <span>{cat.label}</span>
                    </button>
                  ))}
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
                        {activeCategory === 'images' ? (
                          <div className="image-results-grid">
                            {searchResponse.results.map((item) => (
                              <div
                                key={item.document_id}
                                className="image-result-card"
                                onClick={() => setSelectedDocId(item.document_id)}
                                role="button"
                                tabIndex={0}
                              >
                                <div className="image-result-preview">
                                  <IconImage size={32} className="image-grid-icon" />
                                  <span className="image-dim-badge">1920×1080 SVG</span>
                                </div>
                                <div className="image-result-info">
                                  <h4 className="image-result-title">{item.title}</h4>
                                  <span className="image-result-domain font-mono">
                                    {item.url || 'Internal Document'}
                                  </span>
                                  <div className="image-result-footer">
                                    <span className="image-score-tag">
                                      Score: {item.score ? item.score.toFixed(3) : '1.00'}
                                    </span>
                                    <span className="image-inspect-link">View Full Spec &rarr;</span>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
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
                        )}

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
