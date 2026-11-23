import React from 'react';

export function Pagination({ currentPage, totalHits, limit = 10, onPageChange }) {
  const totalPages = Math.ceil(totalHits / limit);

  if (totalPages <= 1) {
    return null;
  }

  // Generate window of page numbers
  const getPageNumbers = () => {
    const pages = [];
    const maxVisible = 5;
    let start = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let end = Math.min(totalPages, start + maxVisible - 1);

    if (end - start + 1 < maxVisible) {
      start = Math.max(1, end - maxVisible + 1);
    }

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    return pages;
  };

  return (
    <nav className="pagination-nav" aria-label="Search results pagination">
      <button
        type="button"
        className="pagination-btn"
        disabled={currentPage <= 1}
        onClick={() => onPageChange(currentPage - 1)}
        aria-label="Previous page"
      >
        ← Previous
      </button>

      <div className="pagination-pages">
        {getPageNumbers().map((p) => (
          <button
            key={p}
            type="button"
            className={`pagination-page-btn ${p === currentPage ? 'active' : ''}`}
            onClick={() => onPageChange(p)}
            aria-current={p === currentPage ? 'page' : undefined}
          >
            {p}
          </button>
        ))}
      </div>

      <button
        type="button"
        className="pagination-btn"
        disabled={currentPage >= totalPages}
        onClick={() => onPageChange(currentPage + 1)}
        aria-label="Next page"
      >
        Next →
      </button>
    </nav>
  );
}
