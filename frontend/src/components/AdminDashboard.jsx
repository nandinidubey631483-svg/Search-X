import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import {
  IconLock,
  IconKey,
  IconGlobe,
  IconTerminal,
  IconActivity,
  IconPlay,
  IconAlertCircle,
  IconSearch,
  IconBookOpen,
  IconLayers,
  IconCheck,
  IconSparkles,
} from './Icons';

export function AdminDashboard({ onSourceAdded }) {
  // Strict in-memory admin authentication state: never persisted to localStorage or cookies
  const [apiKey, setApiKey] = useState('');
  const [keyInput, setKeyInput] = useState('');
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState(null);
  const [authSuccess, setAuthSuccess] = useState(null);

  const [activeSubTab, setActiveSubTab] = useState('sources');

  // Sources State
  const [sources, setSources] = useState([]);
  const [newDomain, setNewDomain] = useState('');
  const [sourcesLoading, setSourcesLoading] = useState(false);
  const [sourcesError, setSourcesError] = useState(null);
  const [sourcesSuccess, setSourcesSuccess] = useState(null);

  // Crawl Jobs State
  const [seedUrls, setSeedUrls] = useState('https://example.com');
  const [allowedDomains, setAllowedDomains] = useState('example.com');
  const [maxDepth, setMaxDepth] = useState(2);
  const [maxPages, setMaxPages] = useState(10);
  const [crawlLoading, setCrawlLoading] = useState(false);
  const [crawlJobResult, setCrawlJobResult] = useState(null);
  const [crawlError, setCrawlError] = useState(null);

  // Analytics State
  const [analytics, setAnalytics] = useState(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [analyticsError, setAnalyticsError] = useState(null);

  // Clean up any legacy localStorage entry for security
  useEffect(() => {
    try {
      localStorage.removeItem('searchx_admin_key');
    } catch {
      // ignore in environments with restricted storage
    }
  }, []);

  const fetchSources = useCallback(async () => {
    if (!apiKey) return;
    setSourcesLoading(true);
    setSourcesError(null);
    try {
      const data = await api.listSources(apiKey);
      setSources(data);
    } catch (err) {
      if (err.status === 401) {
        setSourcesError('Unauthorized (401): Admin session expired or invalid key. Please re-authenticate.');
        setApiKey('');
      } else {
        setSourcesError(err.message || 'Failed to fetch sources. Check your Admin API Key.');
      }
    } finally {
      setSourcesLoading(false);
    }
  }, [apiKey]);

  const fetchAnalytics = useCallback(async () => {
    if (!apiKey) return;
    setAnalyticsLoading(true);
    setAnalyticsError(null);
    try {
      const data = await api.getAnalytics(apiKey);
      setAnalytics(data);
    } catch (err) {
      if (err.status === 401) {
        setAnalyticsError('Unauthorized (401): Admin session expired or invalid key. Please re-authenticate.');
        setApiKey('');
      } else {
        setAnalyticsError(err.message || 'Failed to fetch analytics.');
      }
    } finally {
      setAnalyticsLoading(false);
    }
  }, [apiKey]);

  useEffect(() => {
    if (apiKey) {
      if (activeSubTab === 'sources') fetchSources();
      if (activeSubTab === 'analytics') fetchAnalytics();
    }
  }, [apiKey, activeSubTab, fetchSources, fetchAnalytics]);

  // Authenticate and validate admin API key against backend
  const handleSaveKey = async (e) => {
    if (e) e.preventDefault();
    const clean = keyInput.trim();
    if (!clean) return;

    setAuthLoading(true);
    setAuthError(null);
    setAuthSuccess(null);
    setSourcesError(null);
    setSourcesSuccess(null);

    try {
      // Validate key via protected listSources endpoint
      const data = await api.listSources(clean);
      // Valid key: store strictly in memory
      setApiKey(clean);
      setSources(data);
      setAuthSuccess('Admin authenticated successfully. In-memory session active.');
      setKeyInput('');
    } catch (err) {
      setApiKey('');
      if (err.status === 401 || (err.message && err.message.toLowerCase().includes('unauthorized'))) {
        setAuthError("Unauthorized: Valid admin API key required. Please verify your SEARCHX_ADMIN_KEY.");
      } else {
        setAuthError(err.message || 'Authentication failed. Please verify your credentials and network connection.');
      }
    } finally {
      setAuthLoading(false);
    }
  };

  // Immediate logout: wipe all sensitive in-memory credentials and state
  const handleClearKey = () => {
    setApiKey('');
    setKeyInput('');
    setSources([]);
    setAnalytics(null);
    setAuthError(null);
    setAuthSuccess(null);
    setSourcesError(null);
    setSourcesSuccess(null);
    try {
      localStorage.removeItem('searchx_admin_key');
    } catch {
      // ignore
    }
  };

  const handleAddSource = async (e) => {
    e.preventDefault();
    if (!newDomain.trim()) return;
    let domainToAdd = newDomain.trim().toLowerCase();
    domainToAdd = domainToAdd.replace(/^https?:\/\//i, '').replace(/\/.*$/, '');
    if (!domainToAdd) return;

    setSourcesLoading(true);
    setSourcesError(null);
    setSourcesSuccess(null);
    try {
      await api.addSource({ domain: domainToAdd, enabled: true }, apiKey);
      setNewDomain('');
      setSourcesSuccess(`Domain "${domainToAdd}" was successfully added to the permitted crawl whitelist.`);
      await fetchSources();
      if (onSourceAdded) onSourceAdded();
    } catch (err) {
      if (err.status === 401) {
        setSourcesError('Unauthorized (401): Admin session expired or key invalid. Please re-authenticate.');
        setApiKey('');
      } else {
        setSourcesError(err.message || 'Failed to add permitted domain.');
      }
    } finally {
      setSourcesLoading(false);
    }
  };

  const handleToggleSource = async (source) => {
    setSourcesError(null);
    setSourcesSuccess(null);
    try {
      await api.addSource({ domain: source.domain, enabled: !source.enabled }, apiKey);
      setSourcesSuccess(`Domain "${source.domain}" status updated to ${!source.enabled ? 'Permitted' : 'Blocked'}.`);
      await fetchSources();
    } catch (err) {
      if (err.status === 401) {
        setSourcesError('Unauthorized (401): Admin session expired or key invalid. Please re-authenticate.');
        setApiKey('');
      } else {
        setSourcesError(err.message || 'Failed to update permitted domain.');
      }
    }
  };

  const handleStartCrawl = async (e) => {
    e.preventDefault();
    setCrawlLoading(true);
    setCrawlError(null);
    setCrawlJobResult(null);

    const seeds = seedUrls.split('\n').map((u) => u.trim()).filter(Boolean);
    const domains = allowedDomains.split(',').map((d) => d.trim()).filter(Boolean);

    try {
      const res = await api.startCrawlJob(
        {
          seedUrls: seeds,
          allowedDomains: domains,
          maxDepth,
          maxPages,
        },
        apiKey
      );
      setCrawlJobResult(res);
      if (onSourceAdded) onSourceAdded();
    } catch (err) {
      setCrawlError(err.message || 'Crawl job failed to execute');
    } finally {
      setCrawlLoading(false);
    }
  };

  return (
    <div className="admin-container" data-testid="admin-dashboard">
      {/* SaaS Admin Header */}
      <div className="admin-header-card">
        <div className="admin-header-left">
          <div className="admin-badge-row">
            <span className="admin-pill-tag">Control Center</span>
            <span className="admin-status-indicator">
              <span className="indicator-dot"></span> Live Index
            </span>
          </div>
          <h1 className="admin-title">SearchX Administration</h1>
          <p className="admin-subtitle">
            Manage crawl sources, trigger ingestion pipelines, and monitor inverted index telemetry.
          </p>
        </div>

        {/* API Key Session Controls */}
        <div className="admin-auth-box">
          {apiKey ? (
            <div className="auth-active">
              <div className="auth-key-badge">
                <IconKey size={14} className="auth-icon" />
                <span className="auth-text">Admin Authenticated (In-Memory)</span>
              </div>
              <button type="button" className="btn-logout" onClick={handleClearKey}>
                Lock Session
              </button>
            </div>
          ) : (
            <div className="auth-locked-indicator">
              <IconLock size={14} />
              <span>Session Locked</span>
            </div>
          )}
        </div>
      </div>

      {!apiKey ? (
        <div className="unauthorized-card" data-testid="admin-auth-card">
          <div className="unauthorized-icon">
            <IconLock size={44} />
          </div>
          <h2>Admin Authentication Required</h2>
          <p>
            Please enter your <code>X-Admin-API-Key</code> below to access source management, crawl triggers, and index telemetry.
          </p>

          <form onSubmit={handleSaveKey} className="admin-login-form">
            <div className="login-input-group">
              <input
                type="password"
                className="auth-input login-input-full"
                placeholder="Enter X-Admin-API-Key..."
                value={keyInput}
                onChange={(e) => setKeyInput(e.target.value)}
                aria-label="Admin API Key"
                autoComplete="off"
                disabled={authLoading}
              />
              <button
                type="submit"
                className="btn-primary btn-login-submit"
                disabled={authLoading || !keyInput.trim()}
              >
                {authLoading ? <span className="spinner-white"></span> : 'Unlock'}
              </button>
            </div>
          </form>

          {authError && (
            <div className="error-banner auth-error-banner" role="alert">
              <IconAlertCircle size={16} />
              <span>{authError}</span>
            </div>
          )}

          {authSuccess && (
            <div className="success-banner auth-success-banner" role="status">
              <IconCheck size={16} />
              <span>{authSuccess}</span>
            </div>
          )}

          <div className="security-notice-box">
            <span className="notice-icon">🔒</span>
            <div className="notice-text">
              <strong>In-Memory Isolation:</strong> The admin API key is held strictly in memory for this session and is never persisted to <code>localStorage</code>, cookies, or frontend environment variables.
            </div>
          </div>
        </div>
      ) : (
        <>
          {/* Modern SaaS Segmented Tabs */}
          <div className="admin-nav-tabs">
            <button
              type="button"
              className={`admin-tab-btn ${activeSubTab === 'sources' ? 'active' : ''}`}
              onClick={() => setActiveSubTab('sources')}
            >
              <IconGlobe size={15} /> Allowed Sources ({sources.length})
            </button>
            <button
              type="button"
              className={`admin-tab-btn ${activeSubTab === 'crawl' ? 'active' : ''}`}
              onClick={() => setActiveSubTab('crawl')}
            >
              <IconTerminal size={15} /> Ingestion & Crawl Jobs
            </button>
            <button
              type="button"
              className={`admin-tab-btn ${activeSubTab === 'analytics' ? 'active' : ''}`}
              onClick={() => setActiveSubTab('analytics')}
            >
              <IconActivity size={15} /> Analytics & Metrics
            </button>
          </div>

          {/* TAB 1: Sources */}
          {activeSubTab === 'sources' && (
            <div className="admin-tab-content">
              {/* Add Source Card */}
              <div className="admin-card">
                <div className="card-header-row">
                  <div>
                    <h3>Add Permitted Crawl Domain</h3>
                    <p className="card-desc">
                      Add a trusted website domain. The SearchX crawler strictly respects whitelist constraints.
                    </p>
                  </div>
                </div>

                <form onSubmit={handleAddSource} className="form-inline add-domain-form">
                  <div className="domain-input-wrapper">
                    <span className="input-prefix">https://</span>
                    <input
                      type="text"
                      className="form-input domain-input"
                      placeholder="e.g. docs.python.org"
                      value={newDomain}
                      onChange={(e) => setNewDomain(e.target.value)}
                      required
                    />
                  </div>
                  <button type="submit" className="btn-primary" disabled={sourcesLoading || !newDomain.trim()}>
                    {sourcesLoading ? 'Saving...' : 'Add Source'}
                  </button>
                </form>
              </div>

              {sourcesSuccess && (
                <div className="success-banner" role="status">
                  <IconCheck size={16} /> {sourcesSuccess}
                </div>
              )}

              {sourcesError && (
                <div className="error-banner" role="alert">
                  <IconAlertCircle size={15} /> {sourcesError}
                </div>
              )}

              {/* Configured Sources Table */}
              <div className="admin-card">
                <div className="card-header-row">
                  <div>
                    <h3>Configured Crawl Domains</h3>
                    <p className="card-desc">Active domains approved for web crawling and automated document ingestion.</p>
                  </div>
                  <span className="badge-count">{sources.length} Domains</span>
                </div>

                {sourcesLoading && sources.length === 0 ? (
                  <div className="loading-state-box">Loading configured domains...</div>
                ) : (
                  <div className="table-responsive">
                    <table className="admin-table">
                      <thead>
                        <tr>
                          <th>Target Domain</th>
                          <th>Protocol</th>
                          <th>Security Whitelist</th>
                          <th>Ingestion Status</th>
                          <th>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {sources.map((s) => (
                          <tr key={s.domain}>
                            <td>
                              <div className="domain-cell">
                                <span className="domain-icon">
                                  <IconGlobe size={15} />
                                </span>
                                <span className="domain-name font-mono">{s.domain}</span>
                              </div>
                            </td>
                            <td>
                              <span className="protocol-badge">HTTPS</span>
                            </td>
                            <td>
                              <span className="whitelist-badge">Permitted</span>
                            </td>
                            <td>
                              <span className={`status-pill ${s.enabled ? 'status-enabled' : 'status-disabled'}`}>
                                {s.enabled ? 'Allowed' : 'Blocked'}
                              </span>
                            </td>
                            <td>
                              <button
                                type="button"
                                className={`btn-table-toggle ${s.enabled ? 'btn-disable' : 'btn-enable'}`}
                                onClick={() => handleToggleSource(s)}
                              >
                                {s.enabled ? 'Disable' : 'Enable'}
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: Crawl Jobs */}
          {activeSubTab === 'crawl' && (
            <div className="admin-tab-content">
              <div className="crawl-layout-grid">
                {/* Left Column: Crawler Dispatch */}
                <div className="admin-card crawl-config-pane">
                  <h3>Trigger Controlled Web Ingestion</h3>
                  <p className="card-desc">
                    Dispatch the asynchronous web crawler to fetch, extract, and index documents into the C++ retrieval engine.
                  </p>

                  <form onSubmit={handleStartCrawl} className="crawl-form">
                    <div className="form-group">
                      <label className="form-label" htmlFor="seeds-area">
                        Seed URLs <span className="label-tip">(One per line)</span>:
                      </label>
                      <textarea
                        id="seeds-area"
                        className="form-textarea font-mono"
                        rows={4}
                        value={seedUrls}
                        onChange={(e) => setSeedUrls(e.target.value)}
                        required
                        placeholder="https://example.com"
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label" htmlFor="domains-input">
                        Allowed Domains <span className="label-tip">(Comma-separated)</span>:
                      </label>
                      <input
                        id="domains-input"
                        type="text"
                        className="form-input font-mono"
                        value={allowedDomains}
                        onChange={(e) => setAllowedDomains(e.target.value)}
                        placeholder="example.com, docs.python.org"
                      />
                    </div>

                    <div className="form-row">
                      <div className="form-group">
                        <label className="form-label" htmlFor="depth-input">Max Depth:</label>
                        <input
                          id="depth-input"
                          type="number"
                          className="form-input"
                          min={0}
                          max={5}
                          value={maxDepth}
                          onChange={(e) => setMaxDepth(Number(e.target.value))}
                        />
                      </div>

                      <div className="form-group">
                        <label className="form-label" htmlFor="pages-input">Max Pages:</label>
                        <input
                          id="pages-input"
                          type="number"
                          className="form-input"
                          min={1}
                          max={100}
                          value={maxPages}
                          onChange={(e) => setMaxPages(Number(e.target.value))}
                        />
                      </div>
                    </div>

                    <button
                      type="submit"
                      className="btn-primary btn-crawl-dispatch"
                      disabled={crawlLoading || !seedUrls.trim()}
                    >
                      {crawlLoading ? <span className="spinner-white"></span> : <>
                        <IconPlay size={14} className="btn-inline-icon" /> Start Crawl & Index
                      </>}
                    </button>
                  </form>
                </div>

                {/* Right Column: Live Monitor & Completed Job */}
                <div className="crawl-monitor-pane">
                  {crawlError && (
                    <div className="error-banner">
                      <IconAlertCircle size={15} /> {crawlError}
                    </div>
                  )}

                  {crawlJobResult ? (
                    <div className="admin-card crawl-result-card">
                      <div className="result-card-header">
                        <span className="badge-success">Job Executed</span>
                        <h3>Crawl Job Completed</h3>
                      </div>

                      <div className="stats-grid compact">
                        <div className="stat-box">
                          <span className="stat-label">Job ID</span>
                          <span className="stat-val font-mono">{crawlJobResult.job_id}</span>
                        </div>
                        <div className="stat-box">
                          <span className="stat-label">Execution Status</span>
                          <span className="status-pill status-enabled">{crawlJobResult.status}</span>
                        </div>
                        <div className="stat-box">
                          <span className="stat-label">Pages Crawled</span>
                          <span className="stat-val">{crawlJobResult.pages_crawled}</span>
                        </div>
                        <div className="stat-box">
                          <span className="stat-label">Documents Indexed</span>
                          <span className="stat-val text-success">{crawlJobResult.documents_indexed}</span>
                        </div>
                      </div>

                      {crawlJobResult.errors && Object.keys(crawlJobResult.errors).length > 0 && (
                        <div className="crawl-errors-box">
                          <h4>Crawl Warnings / Exclusions</h4>
                          <ul className="crawl-error-list">
                            {Object.entries(crawlJobResult.errors).map(([url, reason]) => (
                              <li key={url}>
                                <code>{url}</code>: {reason}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="admin-card crawler-idle-card">
                      <span className="idle-icon">
                        <IconTerminal size={32} />
                      </span>
                      <h3>Crawler Pipeline Ready</h3>
                      <p>
                        Configure seed URLs on the left and click <strong>Start Crawl & Index</strong> to launch an ingestion job.
                      </p>
                      <ul className="crawler-checklist">
                        <li>✓ Verifies domain whitelist security restrictions</li>
                        <li>✓ Parses <code>robots.txt</code> and disallows restricted paths</li>
                        <li>✓ Cleans HTML text and extracts outbound links</li>
                        <li>✓ Ingests tokens into C++ Inverted Index and PostgreSQL</li>
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: Analytics */}
          {activeSubTab === 'analytics' && (
            <div className="admin-tab-content">
              {analyticsLoading && <div className="loading-state-box">Loading search and cache analytics...</div>}
              {analyticsError && (
                <div className="error-banner">
                  <IconAlertCircle size={15} /> {analyticsError}
                </div>
              )}

              {analytics && (
                <>
                  {/* KPI Stat Cards */}
                  <div className="stats-grid">
                    <div className="stat-box kpi-card">
                      <div className="kpi-header">
                        <span className="stat-label">Total Searches</span>
                        <span className="kpi-icon">
                          <IconSearch size={20} />
                        </span>
                      </div>
                      <span className="stat-val">{analytics.total_searches}</span>
                      <span className="kpi-sub">Lifetime queries processed</span>
                    </div>

                    <div className="stat-box kpi-card">
                      <div className="kpi-header">
                        <span className="stat-label">Indexed Documents</span>
                        <span className="kpi-icon">
                          <IconBookOpen size={20} />
                        </span>
                      </div>
                      <span className="stat-val text-primary">{analytics.index_stats?.total_documents || 0}</span>
                      <span className="kpi-sub">Active documents in index</span>
                    </div>

                    <div className="stat-box kpi-card">
                      <div className="kpi-header">
                        <span className="stat-label">Vocabulary Size</span>
                        <span className="kpi-icon">
                          <IconLayers size={20} />
                        </span>
                      </div>
                      <span className="stat-val">{analytics.index_stats?.vocabulary_size || 0}</span>
                      <span className="kpi-sub">Unique indexed terms</span>
                    </div>

                    <div className="stat-box kpi-card">
                      <div className="kpi-header">
                        <span className="stat-label">Avg Document Length</span>
                        <span className="kpi-icon">
                          <IconActivity size={20} />
                        </span>
                      </div>
                      <span className="stat-val">{analytics.index_stats?.average_document_length || 0}</span>
                      <span className="kpi-sub">Words per document</span>
                    </div>
                  </div>

                  {/* Cache Metrics */}
                  {analytics.cache_stats && (
                    <div className="admin-card">
                      <div className="card-header-row">
                        <div>
                          <h3>Redis Query Cache Metrics</h3>
                          <p className="card-desc">Sub-millisecond query caching layer with LRU eviction and automatic invalidation.</p>
                        </div>
                        <span className={`status-pill ${analytics.cache_stats.enabled ? 'status-enabled' : 'status-disabled'}`}>
                          {analytics.cache_stats.enabled ? 'Cache Active' : 'Bypassed'}
                        </span>
                      </div>

                      <div className="stats-grid">
                        <div className="stat-box">
                          <span className="stat-label">Cache Hits</span>
                          <span className="stat-val text-success">{analytics.cache_stats.hits}</span>
                        </div>
                        <div className="stat-box">
                          <span className="stat-label">Cache Misses</span>
                          <span className="stat-val text-warning">{analytics.cache_stats.misses}</span>
                        </div>
                        <div className="stat-box">
                          <span className="stat-label">Hit Ratio</span>
                          <span className="stat-val">{(analytics.cache_stats.hit_ratio * 100).toFixed(1)}%</span>
                        </div>
                        <div className="stat-box">
                          <span className="stat-label">TTL Duration</span>
                          <span className="stat-val font-mono">300s</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Top Queries Table with visual popularity */}
                  <div className="admin-card">
                    <div className="card-header-row">
                      <div>
                        <h3>Top Frequent Search Queries</h3>
                        <p className="card-desc">Aggregated query frequencies across all user sessions.</p>
                      </div>
                    </div>

                    {Object.keys(analytics.top_queries || {}).length === 0 ? (
                      <p className="text-muted">No search queries recorded yet.</p>
                    ) : (
                      <div className="table-responsive">
                        <table className="admin-table">
                          <thead>
                            <tr>
                              <th style={{ width: '40%' }}>Query String</th>
                              <th style={{ width: '25%' }}>Executions</th>
                              <th style={{ width: '35%' }}>Relative Popularity</th>
                            </tr>
                          </thead>
                          <tbody>
                            {(() => {
                              const entries = Object.entries(analytics.top_queries);
                              const maxVal = Math.max(...entries.map(([, c]) => c), 1);
                              return entries.map(([q, count]) => {
                                const pct = Math.round((count / maxVal) * 100);
                                return (
                                  <tr key={q}>
                                    <td className="font-semibold">{q}</td>
                                    <td>
                                      <span className="query-count-badge">{count} searches</span>
                                    </td>
                                    <td>
                                      <div className="popularity-bar-container">
                                        <div className="popularity-bar" style={{ width: `${pct}%` }}></div>
                                      </div>
                                    </td>
                                  </tr>
                                );
                              });
                            })()}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
