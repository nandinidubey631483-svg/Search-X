import React from 'react';

export function SearchResultCard({ result, onSelectDocument, queryTerms = [] }) {
  // Highlight matched terms in snippet
  const highlightSnippet = (snippet, terms) => {
    if (!terms || terms.length === 0 || !snippet) return snippet;

    // Build regex pattern for terms
    const cleanTerms = terms.filter(Boolean).map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    if (cleanTerms.length === 0) return snippet;

    const regex = new RegExp(`(${cleanTerms.join('|')})`, 'gi');
    const parts = snippet.split(regex);

    return parts.map((part, i) =>
      regex.test(part) ? (
        <mark key={i} className="highlighted-term">{part}</mark>
      ) : (
        part
      )
    );
  };

  return (
    <article className="result-card" data-testid={`result-${result.document_id}`}>
      <div className="result-header">
        <span className="result-url" title={result.url}>
          {result.url || 'Internal Ingested Document'}
        </span>
        {result.score !== undefined && (
          <span className="result-score" title="Retrieved BM25/TF-IDF score">
            Score: {result.score.toFixed(4)}
          </span>
        )}
      </div>

      <h2 className="result-title">
        <a
          href={result.url || '#'}
          target={result.url ? '_blank' : '_self'}
          rel="noopener noreferrer"
          onClick={(e) => {
            if (!result.url || result.url.startsWith('#')) {
              e.preventDefault();
              onSelectDocument(result.document_id);
            }
          }}
        >
          {result.title || result.document_id}
        </a>
      </h2>

      <p className="result-snippet">
        {highlightSnippet(result.snippet, queryTerms)}
      </p>

      <div className="result-actions">
        <button
          type="button"
          className="btn-view-doc"
          onClick={() => onSelectDocument(result.document_id)}
          aria-label={`View full document ${result.title}`}
        >
          📄 View Full Document ({result.document_id})
        </button>
      </div>
    </article>
  );
}
