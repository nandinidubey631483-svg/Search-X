import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { SearchBar } from '../components/SearchBar';
import { SearchResultCard } from '../components/SearchResultCard';
import { Pagination } from '../components/Pagination';

describe('SearchBar Component', () => {
  it('renders search input and responds to form submit', () => {
    const handleSearch = vi.fn();
    render(
      <SearchBar
        initialQuery=""
        onSearch={handleSearch}
        algo="bm25"
        setAlgo={() => {}}
        mode="any"
        setMode={() => {}}
      />
    );

    const input = screen.getByPlaceholderText(/search documents/i);
    fireEvent.change(input, { target: { value: 'information retrieval' } });
    expect(input.value).toBe('information retrieval');

    const submitBtn = screen.getByRole('button', { name: /search/i });
    fireEvent.click(submitBtn);

    expect(handleSearch).toHaveBeenCalledTimes(1);
    expect(handleSearch).toHaveBeenCalledWith('information retrieval');
  });

  it('toggles filters panel for algorithm and match mode', () => {
    const setAlgo = vi.fn();
    const setMode = vi.fn();

    render(
      <SearchBar
        initialQuery="test"
        onSearch={() => {}}
        algo="bm25"
        setAlgo={setAlgo}
        mode="any"
        setMode={setMode}
      />
    );

    const filterBtn = screen.getByRole('button', { name: /filters/i });
    fireEvent.click(filterBtn);

    const algoSelect = screen.getByLabelText(/ranking algorithm/i);
    expect(algoSelect).toBeInTheDocument();

    fireEvent.change(algoSelect, { target: { value: 'tf_idf' } });
    expect(setAlgo).toHaveBeenCalledWith('tf_idf');
  });
});

describe('SearchResultCard Component', () => {
  it('renders result information and handles document selection', () => {
    const mockResult = {
      document_id: 'doc_bm25',
      title: 'Okapi BM25 Ranking',
      url: 'https://example.com/bm25',
      snippet: 'BM25 is a probabilistic retrieval ranking model.',
      score: 2.3456,
    };
    const handleSelectDoc = vi.fn();

    render(
      <SearchResultCard
        result={mockResult}
        onSelectDocument={handleSelectDoc}
        queryTerms={['bm25']}
      />
    );

    expect(screen.getByText('Okapi BM25 Ranking')).toBeInTheDocument();
    expect(screen.getByText('Score: 2.3456')).toBeInTheDocument();
    expect(screen.getByText(/probabilistic retrieval ranking model/i)).toBeInTheDocument();

    const viewBtn = screen.getByRole('button', { name: /view full document/i });
    fireEvent.click(viewBtn);
    expect(handleSelectDoc).toHaveBeenCalledWith('doc_bm25');
  });
});

describe('Pagination Component', () => {
  it('renders pages and navigates between pages', () => {
    const handlePageChange = vi.fn();
    render(
      <Pagination
        currentPage={1}
        totalHits={25}
        limit={10}
        onPageChange={handlePageChange}
      />
    );

    const prevBtn = screen.getByRole('button', { name: /previous/i });
    const nextBtn = screen.getByRole('button', { name: /next/i });

    expect(prevBtn).toBeDisabled();
    expect(nextBtn).not.toBeDisabled();

    fireEvent.click(nextBtn);
    expect(handlePageChange).toHaveBeenCalledWith(2);

    const page2Btn = screen.getByRole('button', { name: '2' });
    fireEvent.click(page2Btn);
    expect(handlePageChange).toHaveBeenCalledWith(2);
  });
});
