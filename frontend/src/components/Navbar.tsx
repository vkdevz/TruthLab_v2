import React from 'react';

export const Navbar: React.FC = () => {
  return (
    <header className="m-nav">
      <div className="m-container m-nav-inner">
        {/* Brand Wordmark */}
        <a href="#workbench" className="m-logo">
          <span>TruthLab</span>
          <span className="m-logo-badge">v2.0</span>
        </a>

        {/* Quiet Navigation Links */}
        <nav className="m-nav-links">
          <a href="#workbench" className="m-nav-link">Workbench</a>
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
