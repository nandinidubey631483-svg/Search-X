import React, { useEffect } from 'react';
import { IconX, IconExternalLink, IconDownload, IconSearch, IconImage } from './Icons';

export function ImageLightboxModal({ image, onClose, onSearchRelated }) {
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape') onClose();
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!image) return null;

  return (
    <div className="lightbox-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="lightbox-container" onClick={(e) => e.stopPropagation()}>
        {/* Header Bar */}
        <div className="lightbox-header">
          <div className="lightbox-title-wrap">
            <span className="lightbox-category-badge">{image.badge || image.category || 'Visual Media'}</span>
            <h3 className="lightbox-title">{image.title}</h3>
          </div>
          <button
            type="button"
            className="lightbox-close-btn"
            onClick={onClose}
            aria-label="Close Lightbox"
          >
            <IconX size={18} />
          </button>
        </div>

        {/* Image Display Area */}
        <div className="lightbox-media-wrap">
          <img
            src={image.imageUrl || image.url}
            alt={image.title}
            className="lightbox-full-image"
          />
        </div>

        {/* Footer & Meta Details */}
        <div className="lightbox-footer">
          <div className="lightbox-meta">
            <span className="meta-dim font-mono">{image.dim || '3840×2160 UHD'}</span>
            {image.subtitle && <span className="meta-desc">{image.subtitle}</span>}
          </div>

          <div className="lightbox-actions">
            {onSearchRelated && image.query && (
              <button
                type="button"
                className="btn-lightbox-search"
                onClick={() => {
                  onSearchRelated(image.query);
                  onClose();
                }}
              >
                <IconSearch size={14} /> Search Related Docs
              </button>
            )}

            <a
              href={image.imageUrl || image.url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-lightbox-external"
              download
            >
              <IconDownload size={14} /> Full Resolution
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
