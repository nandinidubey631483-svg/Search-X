import React, { useEffect, useState } from 'react';
import { api } from '../services/api';

export function DocumentModal({ documentId, onClose }) {
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!documentId) return;
    setLoading(true);
    setError(null);

    api.getDocument(documentId)
      .then((data) => {
        setDoc(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load document');
        setLoading(false);
      });
  }, [documentId]);

  // Handle ESC key to close modal
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape') onClose();
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!documentId) return null;

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">{doc ? doc.title : 'Loading Document...'}</h2>
          <button type="button" className="modal-close-btn" onClick={onClose} aria-label="Close modal">
            ✕
          </button>
        </div>

        <div className="modal-body">
          {loading && (
            <div className="modal-loading">
              <span className="spinner"></span>
              <p>Retrieving document from backend...</p>
            </div>
          )}

          {error && (
            <div className="modal-error">
              <p>⚠️ {error}</p>
            </div>
          )}

          {doc && (
            <div className="document-details">
              <div className="metadata-grid">
                <div className="meta-item">
                  <span className="meta-label">Document ID:</span>
                  <span className="meta-value">{doc.document_id}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Source URL:</span>
                  <span className="meta-value">
                    {doc.source_url ? (
                      <a href={doc.source_url} target="_blank" rel="noopener noreferrer">
                        {doc.source_url}
                      </a>
                    ) : (
                      'N/A'
                    )}
                  </span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Language:</span>
                  <span className="meta-value">{doc.language || 'en'}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Fetched At:</span>
                  <span className="meta-value">{doc.fetched_at || 'N/A'}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Status:</span>
                  <span className="status-pill">{doc.status || 'ingested'}</span>
                </div>
              </div>

              {doc.description && (
                <div className="doc-section">
                  <h3 className="section-title">Description</h3>
                  <p className="doc-description">{doc.description}</p>
                </div>
              )}

              <div className="doc-section">
                <h3 className="section-title">Full Document Content</h3>
                <div className="doc-content-box">
                  <pre>{doc.content}</pre>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
