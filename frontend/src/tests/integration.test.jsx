import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { App } from '../App';
import { AdminDashboard } from '../components/AdminDashboard';
import { api } from '../services/api';

describe('SearchX App Flow Integration', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it('renders homepage with hero and sample queries', async () => {
    vi.spyOn(api, 'checkHealth').mockResolvedValue({
      status: 'ok',
      version: '1.0.0',
      index_stats: { total_documents: 15, vocabulary_size: 120, average_document_length: 45.2 },
    });

    render(<App />);

    expect(screen.getByText(/A Smarter Search Experience/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /inverted index/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /machine learning/i })).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/Core Online \(15 docs\)/i)).toBeInTheDocument();
    });
  });

  it('executes search and displays results', async () => {
    vi.spyOn(api, 'checkHealth').mockResolvedValue({
      status: 'ok',
      version: '1.0.0',
      index_stats: { total_documents: 5, vocabulary_size: 50, average_document_length: 30 },
    });

    const mockSearchResponse = {
      query: 'inverted',
      total_hits: 1,
      page: 1,
      limit: 10,
      algorithm: 'bm25',
      results: [
        {
          document_id: 'doc_1',
          title: 'Inverted Index Overview',
          url: 'https://example.com/inverted',
          snippet: 'An inverted index stores postings mapping terms to documents.',
          score: 1.89,
        },
      ],
    };
    vi.spyOn(api, 'search').mockResolvedValue(mockSearchResponse);

    render(<App />);

    const searchInput = screen.getByPlaceholderText(/search/i);
    fireEvent.change(searchInput, { target: { value: 'inverted' } });
    fireEvent.submit(searchInput.closest('form'));

    await waitFor(() => {
      expect(screen.getByText('Inverted Index Overview')).toBeInTheDocument();
      expect(screen.getByText(/About/i)).toBeInTheDocument();
    });
  });

  it('renders zero-results card when query matches nothing', async () => {
    vi.spyOn(api, 'checkHealth').mockResolvedValue({ status: 'ok', index_stats: {} });
    vi.spyOn(api, 'search').mockResolvedValue({
      query: 'nonexistent_term',
      total_hits: 0,
      page: 1,
      limit: 10,
      algorithm: 'bm25',
      results: [],
    });

    render(<App />);

    const searchInput = screen.getByPlaceholderText(/search/i);
    fireEvent.change(searchInput, { target: { value: 'nonexistent_term' } });
    fireEvent.submit(searchInput.closest('form'));

    await waitFor(() => {
      expect(screen.getByText(/no matching documents found/i)).toBeInTheDocument();
    });
  });

  it('renders Did You Mean spell correction banner and handles click', async () => {
    vi.spyOn(api, 'checkHealth').mockResolvedValue({ status: 'ok', index_stats: {} });
    const searchSpy = vi.spyOn(api, 'search').mockResolvedValue({
      query: 'pythn',
      total_hits: 1,
      page: 1,
      limit: 10,
      algorithm: 'bm25',
      did_you_mean: 'python',
      is_auto_corrected: false,
      results: [
        {
          document_id: 'doc_1',
          title: 'Python Language Documentation',
          url: 'https://docs.python.org',
          snippet: 'Python is a high-level programming language.',
          score: 1.5,
        },
      ],
    });

    render(<App />);

    const searchInput = screen.getByPlaceholderText(/search/i);
    fireEvent.change(searchInput, { target: { value: 'pythn' } });
    fireEvent.submit(searchInput.closest('form'));

    await waitFor(() => {
      expect(screen.getByText(/did you mean/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'python' })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'python' }));
    await waitFor(() => {
      expect(searchSpy).toHaveBeenCalledWith(
        expect.objectContaining({ query: 'python' })
      );
    });
  });
});

describe('AdminDashboard Component', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('renders unauthorized prompt when no API key provided', () => {
    render(<AdminDashboard />);
    expect(screen.getByText(/admin authentication required/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/enter x-admin-api-key/i)).toBeInTheDocument();
  });

  it('unlocks dashboard and lists sources when valid API key is entered', async () => {
    vi.spyOn(api, 'listSources').mockResolvedValue([
      { domain: 'example.com', enabled: true },
      { domain: 'docs.python.org', enabled: false },
    ]);

    render(<AdminDashboard />);

    const keyInput = screen.getByPlaceholderText(/enter x-admin-api-key/i);
    fireEvent.change(keyInput, { target: { value: 'searchx-admin-secret' } });
    fireEvent.click(screen.getByRole('button', { name: /unlock/i }));

    await waitFor(() => {
      expect(screen.getByText('example.com')).toBeInTheDocument();
      expect(screen.getByText('docs.python.org')).toBeInTheDocument();
      expect(screen.getByText(/Allowed Sources/i)).toBeInTheDocument();
    });
  });
});
