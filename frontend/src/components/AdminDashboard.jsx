import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

export function AdminDashboard({ onSourceAdded }) {
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('searchx_admin_key') || '');
  const [keyInput, setKeyInput] = useState('');
  const [activeSubTab, setActiveSubTab] = useState('sources');

  // Sources State
  const [sources, setSources] = useState([]);
  const [newDomain, setNewDomain] = useState('');
  const [sourcesLoading, setSourcesLoading] = useState(false);
  const [sourcesError, setSourcesError] = useState(null);

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

  const fetchSources = useCallback(async () => {
    if (!apiKey) return;
    setSourcesLoading(true);
    setSourcesError(null);
    try {
      const data = await api.listSources(apiKey);
      setSources(data);
    } catch (err) {
      setSourcesError(err.message || 'Failed to fetch sources. Check your Admin API Key.');
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
      setAnalyticsError(err.message || 'Failed to fetch analytics.');
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

  const handleSaveKey = (e) => {
    e.preventDefault();
    if (!keyInput.trim()) return;
    const clean = keyInput.trim();
    setApiKey(clean);
    localStorage.setItem('searchx_admin_key', clean);
  };

  const handleClearKey = () => {
    setApiKey('');
    setKeyInput('');
    localStorage.removeItem('searchx_admin_key');
    setSources([]);
    setAnalytics(null);
  };

  const handleAddSource = async (e) => {
    e.preventDefault();
    if (!newDomain.trim()) return;
    setSourcesLoading(true);
    try {
      await api.addSource({ domain: newDomain.trim(), enabled: true }, apiKey);
      setNewDomain('');
      await fetchSources();
      if (onSourceAdded) onSourceAdded();
    } catch (err) {
      setSourcesError(err.message || 'Failed to add source');
    } finally {
      setSourcesLoading(false);
    }
  };

  const handleToggleSource = async (source) => {
    try {
      await api.addSource({ domain: source.domain, enabled: !source.enabled }, apiKey);
      await fetchSources();
    } catch (err) {
      setSourcesError(err.message || 'Failed to update source');
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
      <div className="admin-header">
        <div>
          <h1 className="admin-title">SearchX Administration</h1>
          <p className="admin-subtitle">Manage crawl sources, trigger ingestion jobs, and monitor search metrics.</p>
        </div>

        {/* API Key Session Controls */}
        <div className="admin-auth-box">
          {apiKey ? (
            <div className="auth-active">
              <span className="auth-badge">🔑 Admin Key Configured</span>
              <button type="button" className="btn-logout" onClick={handleClearKey}>
                Lock / Logout
              </button>
            </div>
          ) : (
            <form onSubmit={handleSaveKey} className="auth-form">
              <input
                type="password"
                className="auth-input"
                placeholder="Enter X-Admin-API-Key..."
                value={keyInput}
                onChange={(e) => setKeyInput(e.target.value)}
                aria-label="Admin API Key"
              />
              <button type="submit" className="btn-primary" disabled={!keyInput.trim()}>
                Unlock
              </button>
            </form>
          )}
        </div>
      </div>

      {!apiKey ? (
        <div className="unauthorized-card">
          <div className="unauthorized-icon">🔒</div>
          <h2>Admin Authentication Required</h2>
          <p>
            Please enter your <code>X-Admin-API-Key</code> above to access source management, crawl trigger, and analytics.
          </p>
          <p className="hint-text">
            Default local key: <code>searchx-admin-secret</code> (configurable via <code>SEARCHX_ADMIN_KEY</code>).
          </p>
        </div>
      ) : (
        <>
          {/* Sub Navigation Tabs */}
          <div className="admin-tabs">
            <button
              type="button"
              className={`admin-tab-btn ${activeSubTab === 'sources' ? 'active' : ''}`}
              onClick={() => setActiveSubTab('sources')}
            >
              🌐 Allowed Sources ({sources.length})
            </button>
            <button
              type="button"
              className={`admin-tab-btn ${activeSubTab === 'crawl' ? 'active' : ''}`}
              onClick={() => setActiveSubTab('crawl')}
            >
              🕷️ Ingestion & Crawl Jobs
            </button>
            <button
              type="button"
              className={`admin-tab-btn ${activeSubTab === 'analytics' ? 'active' : ''}`}
              onClick={() => setActiveSubTab('analytics')}
            >
              📊 Analytics & Metrics
            </button>
          </div>

          {/* TAB 1: Sources */}
          {activeSubTab === 'sources' && (
            <div className="admin-tab-content">
              <div className="card">
                <h3>Add Permitted Crawl Domain</h3>
                <form onSubmit={handleAddSource} className="form-inline">
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. docs.python.org"
                    value={newDomain}
                    onChange={(e) => setNewDomain(e.target.value)}
                    required
                  />
                  <button type="submit" className="btn-primary" disabled={sourcesLoading || !newDomain.trim()}>
                    {sourcesLoading ? 'Saving...' : 'Add Source'}
                  </button>
                </form>
              </div>

              {sourcesError && <div className="error-banner">⚠️ {sourcesError}</div>}

              <div className="card">
                <h3>Configured Crawl Domains</h3>
                {sourcesLoading && sources.length === 0 ? (
                  <p>Loading configured domains...</p>
                ) : (
                  <div className="table-responsive">
                    <table className="admin-table">
                      <thead>
                        <tr>
                          <th>Domain</th>
                          <th>Status</th>
                          <th>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {sources.map((s) => (
                          <tr key={s.domain}>
                            <td className="font-mono">{s.domain}</td>
                            <td>
                              <span className={`status-pill ${s.enabled ? 'status-enabled' : 'status-disabled'}`}>
                                {s.enabled ? 'Allowed' : 'Blocked'}
                              </span>
                            </td>
                            <td>
                              <button
                                type="button"
                                className="btn-secondary"
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
              <div className="card">
                <h3>Trigger Controlled Web Ingestion</h3>
                <form onSubmit={handleStartCrawl} className="crawl-form">
                  <div className="form-group">
                    <label className="form-label" htmlFor="seeds-area">Seed URLs (one per line):</label>
                    <textarea
                      id="seeds-area"
                      className="form-textarea"
                      rows={3}
                      value={seedUrls}
                      onChange={(e) => setSeedUrls(e.target.value)}
                      required
                    />
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-label" htmlFor="domains-input">Allowed Domains (comma-separated):</label>
                      <input
                        id="domains-input"
                        type="text"
                        className="form-input"
                        value={allowedDomains}
                        onChange={(e) => setAllowedDomains(e.target.value)}
                        placeholder="example.com, docs.python.org"
                      />
                    </div>

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

                  <button type="submit" className="btn-primary" disabled={crawlLoading || !seedUrls.trim()}>
                    {crawlLoading ? <span className="spinner"></span> : '🚀 Start Crawl & Index'}
                  </button>
                </form>
              </div>

              {crawlError && <div className="error-banner">⚠️ {crawlError}</div>}

              {crawlJobResult && (
                <div className="card crawl-result-card">
                  <h3>Crawl Job Completed</h3>
                  <div className="stats-grid">
                    <div className="stat-box">
                      <span className="stat-label">Job ID</span>
                      <span className="stat-val font-mono">{crawlJobResult.job_id}</span>
                    </div>
                    <div className="stat-box">
                      <span className="stat-label">Status</span>
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
                    <div className="crawl-errors">
                      <h4>Crawl Warnings / Exclusions</h4>
                      <ul>
                        {Object.entries(crawlJobResult.errors).map(([url, reason]) => (
                          <li key={url}>
                            <code>{url}</code>: {reason}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: Analytics */}
          {activeSubTab === 'analytics' && (
            <div className="admin-tab-content">
              {analyticsLoading && <p>Loading search and cache analytics...</p>}
              {analyticsError && <div className="error-banner">⚠️ {analyticsError}</div>}

              {analytics && (
                <>
                  <div className="stats-grid">
                    <div className="stat-box">
                      <span className="stat-label">Total Searches</span>
                      <span className="stat-val">{analytics.total_searches}</span>
                    </div>
                    <div className="stat-box">
                      <span className="stat-label">Indexed Documents</span>
                      <span className="stat-val">{analytics.index_stats?.total_documents || 0}</span>
                    </div>
                    <div className="stat-box">
                      <span className="stat-label">Vocabulary Size</span>
                      <span className="stat-val">{analytics.index_stats?.vocabulary_size || 0} terms</span>
                    </div>
                    <div className="stat-box">
                      <span className="stat-label">Avg Document Length</span>
                      <span className="stat-val">{analytics.index_stats?.average_document_length || 0} words</span>
                    </div>
                  </div>

                  {/* Cache Metrics */}
                  {analytics.cache_stats && (
                    <div className="card">
                      <h3>Redis Query Cache Metrics</h3>
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
                          <span className="stat-label">Cache Status</span>
                          <span className={`status-pill ${analytics.cache_stats.enabled ? 'status-enabled' : 'status-disabled'}`}>
                            {analytics.cache_stats.enabled ? 'Active' : 'Bypassed'}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Top Queries Table */}
                  <div className="card">
                    <h3>Top Frequent Search Queries</h3>
                    {Object.keys(analytics.top_queries || {}).length === 0 ? (
                      <p className="text-muted">No search queries recorded yet.</p>
                    ) : (
                      <div className="table-responsive">
                        <table className="admin-table">
                          <thead>
                            <tr>
                              <th>Query String</th>
                              <th>Executions</th>
                            </tr>
                          </thead>
                          <tbody>
                            {Object.entries(analytics.top_queries).map(([q, count]) => (
                              <tr key={q}>
                                <td className="font-semibold">{q}</td>
                                <td>
                                  <span className="query-count-badge">{count}</span>
                                </td>
                              </tr>
                            ))}
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
