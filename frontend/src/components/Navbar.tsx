import React from 'react';

export const Navbar: React.FC = () => {
  return (
    <header className="tl-navbar">
      <div className="tl-navbar-inner">
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div className="tl-brand-icon">TL</div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="tl-brand-text">TruthLab</span>
              <span className="tl-badge tl-badge-blue">v2.0 Research</span>
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              Multimodal Evidence-Aware Adjudication
            </div>
          </div>
        </div>

        {/* Telemetry Indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '4px 12px',
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid var(--border-hairline)',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
            }}
          >
            <span className="tl-pulse-dot"></span>
            <span style={{ color: 'var(--text-secondary)' }}>Online :1234</span>
            <span style={{ color: 'var(--border-hairline)' }}>|</span>
            <span style={{ color: 'var(--status-blue)' }}>T = 1.85</span>
            <span style={{ color: 'var(--border-hairline)' }}>|</span>
            <span style={{ color: 'var(--status-green)' }}>ECE: 0.048</span>
          </div>

          {/* Navigation Links */}
          <nav className="tl-nav-links">
            <a href="#workbench" className="tl-nav-link">Workbench</a>
            <a href="#pipeline" className="tl-nav-link">Pipeline</a>
            <a href="#forensics" className="tl-nav-link">Forensics</a>
            <a href="#benchmarks" className="tl-nav-link">Benchmarks</a>
            <a href="#glossary" className="tl-nav-link">Glossary</a>
            <a
              href="/api/v1/docs"
              target="_blank"
              rel="noreferrer"
              className="tl-btn tl-btn-primary"
              style={{ padding: '5px 12px', fontSize: '0.75rem' }}
            >
              Swagger Docs ↗
            </a>
          </nav>
        </div>
      </div>
    </header>
  );
};
