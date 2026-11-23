/**
 * Isolated API Service Layer for SearchX Frontend.
 * Interacts with FastAPI backend endpoints.
 */

const BASE_URL = import.meta.env.VITE_API_URL || '';

async function handleResponse(response) {
  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    try {
      const data = await response.json();
      if (data.detail) {
        errorDetail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      // response wasn't JSON
    }
    const err = new Error(errorDetail);
    err.status = response.status;
    throw err;
  }
  return response.json();
}

export const api = {
  /**
   * Execute ranked document search.
   */
  async search({ query, algo = 'bm25', mode = 'any', limit = 10, offset = 0 }) {
    const params = new URLSearchParams({
      q: query,
      algo,
      mode,
      limit: String(limit),
      offset: String(offset),
    });
    const res = await fetch(`${BASE_URL}/api/search?${params.toString()}`);
    return handleResponse(res);
  },

  /**
   * Fetch term autocomplete suggestions.
   */
  async getSuggestions(query, limit = 5) {
    if (!query || !query.trim()) return [];
    const params = new URLSearchParams({
      q: query.trim(),
      limit: String(limit),
    });
    const res = await fetch(`${BASE_URL}/api/suggestions?${params.toString()}`);
    const data = await handleResponse(res);
    return data.suggestions || [];
  },

  /**
   * Retrieve document metadata by string ID.
   */
  async getDocument(documentId) {
    const res = await fetch(`${BASE_URL}/api/documents/${encodeURIComponent(documentId)}`);
    return handleResponse(res);
  },

  /**
   * System health check and index stats.
   */
  async checkHealth() {
    const res = await fetch(`${BASE_URL}/api/health`);
    return handleResponse(res);
  },

  /**
   * Admin: list allowed crawl sources.
   */
  async listSources(apiKey) {
    const res = await fetch(`${BASE_URL}/api/admin/sources`, {
      headers: {
        'X-Admin-API-Key': apiKey,
      },
    });
    return handleResponse(res);
  },

  /**
   * Admin: add or update an allowed crawl source.
   */
  async addSource({ domain, enabled = true }, apiKey) {
    const res = await fetch(`${BASE_URL}/api/admin/sources`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Admin-API-Key': apiKey,
      },
      body: JSON.stringify({ domain, enabled }),
    });
    return handleResponse(res);
  },

  /**
   * Admin: start a crawl job.
   */
  async startCrawlJob({ seedUrls, allowedDomains, maxDepth = 2, maxPages = 20 }, apiKey) {
    const res = await fetch(`${BASE_URL}/api/admin/crawl-jobs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Admin-API-Key': apiKey,
      },
      body: JSON.stringify({
        seed_urls: seedUrls,
        allowed_domains: allowedDomains && allowedDomains.length > 0 ? allowedDomains : null,
        max_depth: Number(maxDepth),
        max_pages: Number(maxPages),
      }),
    });
    return handleResponse(res);
  },

  /**
   * Admin: get crawl job status.
   */
  async getCrawlJob(jobId, apiKey) {
    const res = await fetch(`${BASE_URL}/api/admin/crawl-jobs/${encodeURIComponent(jobId)}`, {
      headers: {
        'X-Admin-API-Key': apiKey,
      },
    });
    return handleResponse(res);
  },

  /**
   * Admin: fetch search and index analytics.
   */
  async getAnalytics(apiKey) {
    const res = await fetch(`${BASE_URL}/api/admin/analytics`, {
      headers: {
        'X-Admin-API-Key': apiKey,
      },
    });
    return handleResponse(res);
  },
};
