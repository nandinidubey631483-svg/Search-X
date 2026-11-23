import React from 'react';
import { IconGlobe, IconFileText } from './Icons';

export function SearchResultCard({ result, onSelectDocument, queryTerms = [] }) {
  // Highlight matched terms in snippet
  const highlightSnippet = (snippet, terms) => {
    if (!terms || terms.length === 0 || !snippet) return snippet;

    // Build regex pattern for terms
    const cleanTerms = terms.filter(Boolean).map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    if (cleanTerms.length === 0) return snippet;

    const regex = new RegExp(`(${cleanTerms.join('|')})`, 'gi');
    const parts = snippet.split(regex);

    return parts.map((part, i) =>
      regex.test(part) ? (
        <mark key={i} className="highlighted-term">
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  // Extract domain and clean path for Google-style breadcrumbs
  const getDomainAndPath = (url) => {
    if (!url) return { domain: 'searchx.internal', path: 'documents › ' + result.document_id };
    try {
      const parsed = new URL(url);
      const domain = parsed.hostname;
      const pathParts = parsed.pathname.split('/').filter(Boolean);
      const path = pathParts.length > 0 ? ' › ' + pathParts.slice(0, 3).join(' › ') : '';
      return { domain, path };
    } catch {
      return { domain: url, path: '' };
    }
  };

  const { domain, path } = getDomainAndPath(result.url);

  return (
    <article className="result-card google-style" data-testid={`result-${result.document_id}`}>
      {/* Google-style Breadcrumb / Origin Row */}
      <div className="result-breadcrumb-row">
        <span className="result-favicon">
          <IconGlobe size={15} />
        </span>
        <div className="result-site-info">
          <span className="result-domain">{domain}</span>
          <span className="result-url" title={result.url}>
            {result.url || 'Internal Document'}
          </span>
        </div>
        <div className="result-meta-tags">
          <span className="doc-id-pill">#{result.document_id}</span>
          {result.score !== undefined && (
            <span className="result-score-badge" title="Relevance Score">
              Score: {result.score.toFixed(4)}
            </span>
          )}
        </div>
      </div>

      {/* Main Title Link */}
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
          className="result-link"
        >
          {result.title || result.document_id}
        </a>
      </h2>

      {/* Snippet with Keywords Highlighted */}
      <p className="result-snippet">{highlightSnippet(result.snippet, queryTerms)}</p>

      {/* Bottom Action Footer */}
      <div className="result-card-footer">
        <button
          type="button"
          className="btn-view-doc"
          onClick={() => onSelectDocument(result.document_id)}
          aria-label={`View full document ${result.title}`}
        >
          <IconFileText size={14} className="btn-inline-icon" /> View Full Document ({result.document_id})
        </button>
        {result.url && (
          <a
            href={result.url}
            target="_blank"
            rel="noopener noreferrer"
            className="external-link-btn"
            title="Open original website"
          >
            Visit Website ↗
          </a>
        )}
      </div>
    </article>
  );
}
