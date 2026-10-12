import React from 'react';

export const Navbar: React.FC = () => {
  return (
    <header className="m-nav">
      <div className="m-container m-nav-inner">
        {/* Brand Wordmark */}
        <a href="#workbench" className="m-logo">
          <svg width="20" height="20" viewBox="0 0 64 64" fill="none" aria-hidden="true" style={{ flexShrink: 0 }}>
            <rect x="2" y="2" width="60" height="60" rx="14" fill="#121215" stroke="#27272A" strokeWidth="3" />
            <path d="M32 14L48 22V34C48 43.5 41.2 51.2 32 53.5C22.8 51.2 16 43.5 16 34V22L32 14Z" fill="#09090B" stroke="#FAFAFA" strokeWidth="3" strokeLinejoin="round" />
            <path d="M25 33.5L30 38.5L40 27.5" stroke="#22C55E" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <span>TruthLab</span>
        </a>

        {/* Quiet Navigation Links */}
        <nav className="m-nav-links">
          <a href="#workbench" className="m-nav-link">Verify</a>
          <a href="#architecture" className="m-nav-link">Architecture</a>
          <a href="#benchmarks" className="m-nav-link">Benchmarks</a>
          <a href="#methodology" className="m-nav-link">Methodology</a>
          <a
            href="/api/v1/docs"
            target="_blank"
            rel="noreferrer"
            className="m-nav-link"
            style={{ color: 'var(--text-primary)' }}
          >
            API Docs ↗
          </a>
        </nav>
      </div>
    </header>
  );
};
