import React from 'react';

export const ForensicsDeepDive: React.FC = () => {
  return (
    <section id="forensics" className="tl-section">
      <div className="tl-container">
        <div className="tl-section-header">
          <span className="tl-tag">// FORENSIC SIGNAL ANALYSIS</span>
          <h2 className="tl-title">Multi-Layer Forensic Modalities</h2>
          <p className="tl-desc">
            Unlike black-box models that issue opaque predictions, TruthLab inspects mathematical compression residuals,
            discrete frequency distributions, and audio-visual temporal alignment to expose manipulation.
          </p>
        </div>

        <div className="tl-grid-2">
          {/* Module A: Error Level Analysis */}
          <div className="tl-card">
            <div className="tl-card-header">
              <h3 className="tl-card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--status-blue)' }}></span>
                Error Level Analysis (ELA)
              </h3>
              <span className="tl-badge tl-badge-blue">Compression Residuals</span>
            </div>
            <p className="tl-card-text">
              When an image is saved in JPEG format, its discrete cosine transform (DCT) coefficients are quantized
              at an approximately uniform error rate. If an object is digitally spliced in from an external source or edited,
              its localized error rate diverges from the rest of the image.
            </p>

            <div className="tl-code-box" style={{ marginBottom: '14px' }}>
              <div style={{ color: 'var(--text-muted)' }}>// Differential Matrix Calculation (Q = 90)</div>
              <div style={{ color: 'var(--status-blue)' }}>ΔI(x, y) = |I_orig(x, y) - I_resaved(x, y)|</div>
              <div style={{ color: 'var(--text-muted)', marginTop: '4px' }}>// Regional 16x16 DCT Block Variance</div>
              <div style={{ color: 'var(--text-primary)' }}>Variance_block &gt; (Mean_diff * 2.5 + 0.05) → Splicing</div>
            </div>

            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
              <strong style={{ color: 'var(--text-secondary)' }}>Academic Guardrail:</strong> ELA identifies compression irregularities;
              it is integrated with retrieved evidence rather than treated as unilateral proof, preventing false positives from social media re-compression.
            </div>
          </div>

          {/* Module B: Synthetic Media Heuristics */}
          <div className="tl-card">
            <div className="tl-card-header">
              <h3 className="tl-card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--status-indigo)' }}></span>
                Synthetic Diffusion Frequency (σ²_∇²)
              </h3>
              <span className="tl-badge tl-badge-blue">Frequency Domain</span>
            </div>
            <p className="tl-card-text">
              Generative diffusion models (Midjourney, DALL-E, Stable Diffusion) exhibit characteristic
              high-saturation dispersion profiles and unnatural Laplacian gradient smoothness along structural boundaries.
            </p>

            <div className="tl-code-box" style={{ marginBottom: '14px' }}>
              <div style={{ color: 'var(--text-muted)' }}>// Discrete Laplacian Spatial Second-Derivative</div>
              <div style={{ color: 'var(--status-indigo)' }}>σ²_∇² = Var(∂²I/∂x²) + Var(∂²I/∂y²)</div>
              <div style={{ color: 'var(--text-muted)', marginTop: '4px' }}>// Prior-Bounded Continuous Likelihood</div>
              <div style={{ color: 'var(--status-green)' }}>P(synthetic) ∈ [0.05, 0.95] (Strictly Bounded)</div>
            </div>

            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
              <strong style={{ color: 'var(--text-secondary)' }}>Anti-Overconfidence Bound:</strong> Synthetic likelihood is bounded to [0.05, 0.95]
              to explicitly reject false absolute certainties, accommodating camera noise profiles and compression artifacts.
            </div>
          </div>

          {/* Module C: Video Audio-Visual Dual Channel */}
          <div className="tl-card">
            <div className="tl-card-header">
              <h3 className="tl-card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--status-amber)' }}></span>
                Whisper ASR & Scene Chyron Alignment
              </h3>
              <span className="tl-badge tl-badge-amber">Cross-Modal Temporal</span>
            </div>
            <p className="tl-card-text">
              Video misinformation frequently pairs genuine video footage with deceptive audio, or overlays false "BREAKING NEWS"
              tickers over unrelated clips. TruthLab demuxes both streams in parallel:
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '14px' }}>
              <div className="tl-code-box">
                <span style={{ color: 'var(--status-amber)', display: 'block', fontWeight: 600, marginBottom: '2px' }}>Audio Track:</span>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>16kHz Mono WAV → Whisper ASR speech segments</span>
              </div>
              <div className="tl-code-box">
                <span style={{ color: 'var(--status-blue)', display: 'block', fontWeight: 600, marginBottom: '2px' }}>Visual Track:</span>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Keyframe scene OCR → Chyron & banner texts</span>
              </div>
            </div>

            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
              Both text corpora are unified into atomic propositions and queried simultaneously, exposing out-of-context audio overdubs.
            </div>
          </div>

          {/* Module D: Epistemic Refusal vs Hallucination */}
          <div className="tl-card">
            <div className="tl-card-header">
              <h3 className="tl-card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--status-green)' }}></span>
                Epistemic Refusal & Temporal Decay
              </h3>
              <span className="tl-badge tl-badge-green">Hallucination Guard</span>
            </div>
            <p className="tl-card-text">
              Standard LLMs hallucinate assertions when presented with uninformative imagery. TruthLab incorporates
              academic refusal thresholds and time-decay rules:
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', background: 'var(--bg-code)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-hairline)', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Non-textual / Artistic Media:</span>
                <span style={{ color: 'var(--status-amber)', fontWeight: 600 }}>INSUFFICIENT_EVIDENCE</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', background: 'var(--bg-code)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-hairline)', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Evidence Sufficiency &lt; 1.20:</span>
                <span style={{ color: 'var(--status-blue)', fontWeight: 600 }}>Withhold Speculation</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', background: 'var(--bg-code)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-hairline)', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Context Delta &gt; 180 Days:</span>
                <span style={{ color: 'var(--status-indigo)', fontWeight: 600 }}>Flag as OUTDATED</span>
              </div>
            </div>

            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
              Guarantees that the system refuses to speculate on ungrounded claims or recycled historical notices.
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
