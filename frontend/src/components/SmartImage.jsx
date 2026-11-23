import React, { useState } from 'react';
import { IconImage, IconMaximize2 } from './Icons';

/**
 * SmartImage renders a high-res image with shimmer skeleton loading,
 * and a rich procedural SVG vector fallback if the network blocks the image.
 */
export function SmartImage({
  src,
  alt = 'Image Preview',
  className = '',
  aspectRatio = '16/9',
  category = 'Visual Media',
  onPreviewClick = null,
}) {
  const [loaded, setLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);

  // Gradient presets for fallback diagrams based on category
  const gradients = {
    wallpaper: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #ec4899 100%)',
    schematic: 'linear-gradient(135deg, #0ea5e9 0%, #2563eb 50%, #1d4ed8 100%)',
    vector: 'linear-gradient(135deg, #8b5cf6 0%, #d946ef 50%, #f43f5e 100%)',
    default: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%)',
  };

  const bgGrad = gradients[category?.toLowerCase()] || gradients.default;

  return (
    <div
      className={`smart-image-container ${className} ${loaded ? 'is-loaded' : 'is-loading'}`}
      style={{ aspectRatio }}
      onClick={onPreviewClick}
      role={onPreviewClick ? 'button' : undefined}
      tabIndex={onPreviewClick ? 0 : undefined}
    >
      {/* Shimmer Placeholder */}
      {!loaded && !hasError && (
        <div className="smart-image-shimmer" aria-hidden="true">
          <div className="shimmer-wave"></div>
          <IconImage size={24} className="shimmer-icon" />
        </div>
      )}

      {/* Primary Image */}
      {!hasError && src ? (
        <img
          src={src}
          alt={alt}
          loading="lazy"
          className={`smart-image-element ${loaded ? 'visible' : 'hidden'}`}
          onLoad={() => setLoaded(true)}
          onError={() => setHasError(true)}
        />
      ) : (
        /* Bulletproof SVG Graphic Fallback */
        <div className="smart-image-fallback" style={{ background: bgGrad }}>
          <div className="fallback-grid-overlay"></div>
          <div className="fallback-content">
            <svg
              className="fallback-vector-graphic"
              viewBox="0 0 100 60"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <rect x="5" y="5" width="90" height="50" rx="6" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" strokeDasharray="3 3" />
              <circle cx="30" cy="25" r="8" fill="rgba(255,255,255,0.85)" />
              <path d="M12 48L32 30L48 42L65 24L88 48H12Z" fill="rgba(255,255,255,0.3)" />
              <path d="M40 48L55 35L70 48H40Z" fill="rgba(255,255,255,0.4)" />
              <circle cx="75" cy="18" r="3" fill="rgba(255,255,255,0.9)" />
            </svg>
            <span className="fallback-tag">{category}</span>
          </div>
        </div>
      )}

      {/* Hover Zoom Overlay */}
      {onPreviewClick && (
        <div className="smart-image-hover-overlay">
          <span className="overlay-preview-btn">
            <IconMaximize2 size={16} /> Expand
          </span>
        </div>
      )}
    </div>
  );
}
