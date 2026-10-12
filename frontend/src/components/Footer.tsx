import React, { useState } from 'react';

export const Footer: React.FC = () => {
  const [activeSnippet, setActiveSnippet] = useState<'CURL' | 'PYTHON'>('CURL');

  const curlSnippet = `# Verify an image with ELA and OCR forensics
curl -X POST "http://localhost:1234/api/v1/verify/image" \\
  -H "accept: application/json" \\
  -F "file=@sample_5g_meme.png;type=image/png"`;

  const pythonSnippet = `import httpx

# Async verification of video clip
async with httpx.AsyncClient() as client:
    with open("news_clip.mp4", "rb") as f:
        response = await client.post(
            "http://localhost:1234/api/v1/verify/video",
            files={"file": ("news_clip.mp4", f, "video/mp4")},
            timeout=30.0
        )
    print(response.json()["overall_veracity"])`;

  const bibtexCitation = `@article{truthlab2026multimodal,
  title={Multimodal Evidence-Aware Misinformation Verification with Calibrated Epistemics},
  author={TruthLab Research Team},
  journal={Major Project Defense Dissertation},
  year={2026},
  institution={TruthLab Research Laboratory},
  url={http://localhost:1234}
}`;

  return (
    <footer id="api" style={{ background: '#080a0f', borderTop: '1px solid var(--border-hairline)', padding: '64px 0 32px 0' }}>
      <div className="tl-container">
        <div className="tl-grid-2" style={{ marginBottom: '48px' }}>
          {/* API Invocation */}
          <div className="tl-card">
            <div className="tl-card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: 'var(--status-green)' }}></span>
                API Client Invocation
              </div>
              <div style={{ display: 'flex', gap: '4px' }}>
                <button
                  onClick={() => setActiveSnippet('CURL')}
                  className="tl-btn"
                  style={{
                    padding: '4px 10px',
                    fontSize: '0.72rem',
                    fontFamily: 'var(--font-mono)',
                    background: activeSnippet === 'CURL' ? 'var(--status-indigo)' : 'transparent',
                    color: activeSnippet === 'CURL' ? '#fff' : 'var(--text-muted)',
                  }}
                >
                  cURL
                </button>
                <button
                  onClick={() => setActiveSnippet('PYTHON')}
                  className="tl-btn"
                  style={{
                    padding: '4px 10px',
                    fontSize: '0.72rem',
                    fontFamily: 'var(--font-mono)',
                    background: activeSnippet === 'PYTHON' ? 'var(--status-indigo)' : 'transparent',
                    color: activeSnippet === 'PYTHON' ? '#fff' : 'var(--text-muted)',
                  }}
                >
                  Python
                </button>
              </div>
            </div>

            <pre className="tl-code-box" style={{ fontSize: '0.74rem', color: 'var(--status-blue)', marginBottom: '12px' }}>
              <code>{activeSnippet === 'CURL' ? curlSnippet : pythonSnippet}</code>
            </pre>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Interactive Schema:</span>
              <a
                href="/api/v1/docs"
                target="_blank"
                rel="noreferrer"
                style={{ color: 'var(--status-indigo)', textDecoration: 'none' }}
              >
                Open OpenAPI / Swagger Docs ↗
              </a>
            </div>
          </div>

          {/* BibTeX Citation */}
          <div className="tl-card">
            <div className="tl-card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: 'var(--status-indigo)' }}></span>
                Academic Citation (BibTeX)
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                Dissertation Defense
              </span>
            </div>

            <pre className="tl-code-box" style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
              <code>{bibtexCitation}</code>
            </pre>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Research Artifacts:</span>
              <span style={{ color: 'var(--text-secondary)' }}>DATASET_AUDIT.md • RESEARCH_TABLES.md</span>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div
          style={{
            borderTop: '1px solid var(--border-hairline)',
            paddingTop: '24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '16px',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.72rem',
            color: 'var(--text-muted)',
          }}
        >
          <div>TruthLab v2.0 • Multimodal Evidence-Aware Misinformation Verification System</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <a href="#workbench" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>Top ↑</a>
            <span>•</span>
            <a href="/api/v1/health" target="_blank" rel="noreferrer" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>
              System Health
            </a>
            <span>•</span>
            <span style={{ color: 'var(--status-green)' }}>Operational on :1234</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
