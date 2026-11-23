import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api } from '../services/api';

describe('SearchX API Service Layer', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('search constructs URL and calls backend GET', async () => {
    const mockResponse = {
      query: 'inverted index',
      total_hits: 1,
      page: 1,
      limit: 10,
      algorithm: 'bm25',
      results: [],
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    });

    const res = await api.search({
      query: 'inverted index',
      algo: 'bm25',
      mode: 'all',
      limit: 10,
      offset: 0,
    });

    expect(fetch).toHaveBeenCalledTimes(1);
    const calledUrl = fetch.mock.calls[0][0];
    expect(calledUrl).toContain('/api/search?');
    expect(calledUrl).toContain('q=inverted+index');
    expect(calledUrl).toContain('algo=bm25');
    expect(calledUrl).toContain('mode=all');
    expect(res).toEqual(mockResponse);
  });

  it('getSuggestions fetches autocomplete terms', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ query: 'in', suggestions: ['index', 'inverted'] }),
    });

    const suggestions = await api.getSuggestions('in', 5);
    expect(suggestions).toEqual(['index', 'inverted']);
  });

  it('getDocument fetches document metadata by ID', async () => {
    const mockDoc = {
      document_id: 'doc_123',
      title: 'Title 123',
      content: 'Body content',
    };
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockDoc,
    });

    const doc = await api.getDocument('doc_123');
    expect(doc).toEqual(mockDoc);
    expect(fetch.mock.calls[0][0]).toContain('/api/documents/doc_123');
  });

  it('listSources attaches X-Admin-API-Key header', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [{ domain: 'example.com', enabled: true }],
    });

    const sources = await api.listSources('test-admin-key');
    expect(sources).toHaveLength(1);
    const headers = fetch.mock.calls[0][1].headers;
    expect(headers['X-Admin-API-Key']).toBe('test-admin-key');
  });

  it('startCrawlJob sends POST request with parameters', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ job_id: 'job_1', status: 'completed' }),
    });

    const job = await api.startCrawlJob(
      {
        seedUrls: ['https://example.com'],
        allowedDomains: ['example.com'],
        maxDepth: 1,
        maxPages: 5,
      },
      'test-key'
    );

    expect(job.job_id).toBe('job_1');
    expect(fetch.mock.calls[0][1].method).toBe('POST');
  });

  it('throws error with detail when request fails', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'Document doc_missing not found' }),
    });

    await expect(api.getDocument('doc_missing')).rejects.toThrow('Document doc_missing not found');
  });
});
