import React, { useState } from 'react';

export const MethodologySection: React.FC = () => {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(0);

  const methods = [
    {
      title: "Error Level Analysis (ELA)",
      metric: "ΔI(x,y) = |I_orig - I_resaved| @ Q=90",
      desc: "Re-saves imagery at a standardized JPEG quantization table to identify localized compression anomalies. Digital splicing and modifications exhibit divergent error rates across 16x16 DCT blocks."
    },
    {
      title: "Synthetic Media Heuristics",
      metric: "σ²_∇² = Var(∂²I/∂x²) + Var(∂²I/∂y²)",
      desc: "Discrete 2D second-derivative spatial convolution measuring high-frequency structural edge variance. Identifies the characteristic ultra-smooth textures of diffusion generative models, strictly bounded in [0.05, 0.95]."
    },
    {
      title: "Whisper ASR Speech-to-Text",
      metric: "16kHz Mono PCM WAV Demuxing",
      desc: "FFmpeg demuxes audio tracks into single-channel 16kHz linear PCM WAV format before passing audio frames to the Whisper Transformer encoder-decoder to yield timestamped dialogue transcripts."
    },
    {
      title: "Scene Chyron OCR",
      metric: "Adaptive Otsu Thresholding",
      desc: "Samples keyframes at scene transitions to transcribe on-screen breaking news tickers and lower-third graphics, cross-referencing visual claims against spoken dialogue."
    },
    {
      title: "Epistemic Refusal Guard",
      metric: "Sufficiency Score < 1.20 → Withhold",
      desc: "If evidence sufficiency falls below 1.20 or an image contains no legible text, the system safely outputs INSUFFICIENT_EVIDENCE with calibrated uncertainty rather than fabricating claims."
    },
    {
      title: "Anti-SSRF Network Shield",
      metric: "RFC 1918 / RFC 3927 DNS Hook",
      desc: "Pre-fetch DNS resolution filters destination hostnames prior to HTTP request dispatch. Rejects private, loopback, link-local, and cloud metadata IPs to prevent internal intranet scanning."
    }
  ];

  return (
    <section id="methodology" className="m-section">
      <div className="m-container">
        <div className="m-section-label">Methodology</div>
        <h2 className="m-section-title">Detection Models & Security Guards</h2>
        <p className="m-section-sub">
          Mathematical formulations, signal processing heuristics, and network security filters implemented across the system.
        </p>

        {/* Desktop 2-Column Grid */}
        <div className="m-grid-2 m-desktop-only">
          {methods.map((m, idx) => (
            <div key={idx} className="m-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '8px' }}>
                <h3 className="m-card-title">{m.title}</h3>
              </div>
              <div className="m-code" style={{ marginBottom: '12px' }}>
                {m.metric}
              </div>
              <p className="m-card-desc">{m.desc}</p>
            </div>
          ))}
        </div>

        {/* Dedicated Mobile Accordion Stack (Miller's Law Cognitive Load Reduction) */}
        <div className="m-mobile-only" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {methods.map((m, idx) => {
            const isOpen = expandedIdx === idx;
            return (
              <div key={idx} className="m-card" style={{ padding: '14px 16px' }}>
                <button
                  type="button"
                  onClick={() => setExpandedIdx(isOpen ? null : idx)}
                  style={{
                    width: '100%',
                    background: 'none',
                    border: 'none',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    cursor: 'pointer',
                    padding: 0,
                    color: 'var(--text-primary)',
                    textAlign: 'left',
                  }}
                >
                  <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>{m.title}</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    {isOpen ? '−' : '+'}
                  </span>
                </button>
                {isOpen && (
                  <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)' }}>
                    <div className="m-code" style={{ marginBottom: '10px', fontSize: '0.74rem' }}>
                      {m.metric}
                    </div>
                    <p className="m-card-desc" style={{ fontSize: '0.8rem' }}>{m.desc}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
