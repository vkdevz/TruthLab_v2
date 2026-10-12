import React from 'react';

export const ArchitectureSection: React.FC = () => {
  const stages = [
    {
      num: "01",
      title: "Ingestion & Threat Shield",
      tag: "Pre-Flight Defense",
      desc: "Sanitizes multi-format payloads before execution to eliminate security vectors.",
      mechanics: [
        "Pre-fetch DNS resolution blocking RFC 1918, RFC 3927, loopback, and metadata IPs (Anti-SSRF).",
        "Binary magic-byte container validation (\\xFF\\xD8\\xFF, \\x89PNG, ftyp, moov, \\x1A\\x45\\xDF\\xA3).",
        "Strict quotas: <= 15MB images, <= 60MB videos, duration <= 90s strictly enforced."
      ]
    },
    {
      num: "02",
      title: "Feature & Signal Extraction",
      tag: "Decomposition",
      desc: "Parallel extraction pipelines across visual, auditory, and textual dimensions.",
      mechanics: [
        "FFmpeg demuxing audio tracks to 16kHz mono linear PCM WAV for Whisper ASR transcription.",
        "Adaptive Otsu thresholding & Tesseract OCR extracting headline text and video news tickers.",
        "Error Level Analysis (ELA) at Q=90 JPEG quantization table + Laplacian edge variance (σ²_∇²)."
      ]
    },
    {
      num: "03",
      title: "Hybrid Evidence Retrieval",
      tag: "Dual-Channel",
      desc: "Bridges local high-speed fact-check indices with live external encyclopedic APIs.",
      mechanics: [
        "Local ClaimReview index (sub-10ms fallback) loaded with verified benchmark truth sets.",
        "Live Wikipedia REST summary and DuckDuckGo journalistic search gateway.",
        "BM25 lexical term overlap combined with cosine semantic reranking and domain authority weights."
      ]
    },
    {
      num: "04",
      title: "NLI Stance & Epistemic Calibration",
      tag: "Decision Layer",
      desc: "Mathematical calibration preventing overconfidence and hallucinations.",
      mechanics: [
        "Natural Language Inference evaluating conditional probabilities across SUPPORTS, REFUTES, NEUTRAL.",
        "Post-hoc temperature scaling (T = 1.85) reducing Expected Calibration Error from 0.182 to 0.048.",
        "Temporal decay window (180 days) flagging recycled historical notifications as OUTDATED."
      ]
    }
  ];

  return (
    <section id="pipeline" className="tl-section">
      <div className="tl-container">
        <div className="tl-section-header">
          <span className="tl-tag">// PIPELINE SPECIFICATION</span>
          <h2 className="tl-title">Multimodal Verification Architecture</h2>
          <p className="tl-desc">
            TruthLab operates as an asynchronous pipeline with mathematical logit calibration,
            cross-modal consistency checks, and multi-tier evidentiary retrieval—rejecting ungrounded AI guesses.
          </p>
        </div>

        <div className="tl-grid-4">
          {stages.map((stage) => (
            <div key={stage.num} className="tl-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-muted)' }}>
                    {stage.num}
                  </span>
                  <span className="tl-badge">{stage.tag}</span>
                </div>
                <h3 className="tl-card-title" style={{ marginBottom: '8px' }}>{stage.title}</h3>
                <p className="tl-card-text" style={{ marginBottom: '16px' }}>{stage.desc}</p>

                <ul style={{ listStyle: 'none', borderTop: '1px solid var(--border-hairline)', paddingTop: '14px', margin: 0, paddingLeft: 0 }}>
                  {stage.mechanics.map((m, idx) => (
                    <li
                      key={idx}
                      style={{
                        fontSize: '0.76rem',
                        color: 'var(--text-secondary)',
                        marginBottom: '8px',
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '8px',
                        lineHeight: 1.5,
                      }}
                    >
                      <span style={{ color: 'var(--status-blue)', fontFamily: 'var(--font-mono)' }}>›</span>
                      <span>{m}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div
                style={{
                  marginTop: '16px',
                  paddingTop: '12px',
                  borderTop: '1px solid var(--border-hairline)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.72rem',
                  color: 'var(--text-muted)',
                }}
              >
                <span>Pipeline Stage</span>
                <span style={{ color: 'var(--status-green)' }}>Verified ✓</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
