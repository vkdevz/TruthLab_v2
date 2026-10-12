import React, { useState } from 'react';

export const Footer: React.FC = () => {
  const [showCitation, setShowCitation] = useState(false);

  const bibtex = `@article{truthlab2026multimodal,
  title={Multimodal Evidence-Aware Misinformation Verification with Calibrated Epistemics},
  author={TruthLab Research Team},
  year={2026},
  institution={TruthLab Research Laboratory},
  url={http://localhost:1234}
}`;

  return (
    <footer style={{ borderTop: '1px solid var(--border-subtle)', padding: '64px 0 40px 0', background: 'var(--bg-base)' }}>
      <div className="m-container">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '32px', marginBottom: '48px' }}>
          <div>
            <div style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-primary)', marginBottom: '6px' }}>
              TruthLab
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', maxWidth: '420px', lineHeight: 1.6 }}>
              Major project research implementation for multimodal factual claim verification and forensic signal extraction.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '32px', fontSize: '0.82rem' }}>
            <div>
              <div style={{ color: 'var(--text-primary)', fontWeight: 500, marginBottom: '10px' }}>Resources</div>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <li><a href="/api/v1/docs" target="_blank" rel="noreferrer" className="m-nav-link">Interactive Swagger Docs ↗</a></li>
                <li><a href="/api/v1/health" target="_blank" rel="noreferrer" className="m-nav-link">System Health API ↗</a></li>
                <li><button onClick={() => setShowCitation(!showCitation)} style={{ background: 'none', border: 'none', padding: 0, font: 'inherit', color: 'var(--text-muted)', cursor: 'pointer', textAlign: 'left' }} className="m-nav-link">BibTeX Citation {showCitation ? '▲' : '▼'}</button></li>
              </ul>
            </div>
          </div>
        </div>

        {showCitation && (
          <div style={{ marginBottom: '32px' }}>
            <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: '8px' }}>
              Academic Citation (BibTeX):
            </div>
            <pre className="m-code">
              <code>{bibtex}</code>
            </pre>
          </div>
        )}

        <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          <div>TruthLab • Major Project 2026</div>
          <div>Operating on localhost:1234</div>
        </div>
      </div>
    </footer>
  );
};
