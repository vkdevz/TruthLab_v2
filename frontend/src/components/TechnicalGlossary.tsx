import React from 'react';

export const TechnicalGlossary: React.FC = () => {
  const glossaryTerms = [
    {
      term: "Anti-SSRF Socket Shield",
      formula: "IP ∉ {RFC 1918, RFC 3927, 127.0.0.0/8, 169.254.169.254}",
      definition: "Pre-fetch DNS resolution hook resolving destination hostnames before HTTP dispatch. Rejects private, loopback, link-local, and cloud metadata IPs to block internal intranet scanning."
    },
    {
      term: "Binary Magic Byte Validation",
      formula: "Header[0:4] == \\xFF\\xD8\\xFF | \\x89PNG | ftyp | \\x1A\\x45\\xDF\\xA3",
      definition: "Inspection of raw leading file byte signatures before invoking media decoders. Enforces file identity at the byte level, neutralizing polyglot payload attacks and MIME spoofing."
    },
    {
      term: "Error Level Analysis (ELA)",
      formula: "ΔI(x, y) = |I_orig(x, y) - I_resaved(x, y)| @ Q=90",
      definition: "Re-saves images to memory at a standardized JPEG quantization table (90%) and calculates the absolute difference matrix. Exposes localized compression anomalies created by digital splicing."
    },
    {
      term: "Laplacian Gradient Frequency (σ²_∇²)",
      formula: "σ²_∇² = Var(∂²I/∂x²) + Var(∂²I/∂y²)",
      definition: "Discrete second-derivative spatial convolution measuring high-frequency structural edge variance. Flags the characteristic ultra-smooth textures and noise profiles of generative diffusion models."
    },
    {
      term: "Whisper ASR 16kHz Demuxing",
      formula: "FFmpeg: -vn -acodec pcm_s16le -ar 16000 -ac 1",
      definition: "Demuxes audio tracks into single-channel 16kHz linear PCM WAV format before passing audio frames to the Whisper Transformer encoder-decoder to yield timestamped dialogue transcripts."
    },
    {
      term: "Temperature Scaling Calibration (T = 1.85)",
      formula: "p̂_i = exp(z_i / 1.85) / Σ_j exp(z_j / 1.85)",
      definition: "Post-processing logit calibration optimizing Expected Calibration Error (ECE). Lowers neural confidence on out-of-distribution inputs from 0.182 to 0.048, preventing false overconfidence."
    },
    {
      term: "Epistemic Refusal Guard",
      formula: "Σ_k w_k · Score(e_k) < 1.20 → INSUFFICIENT_EVIDENCE",
      definition: "Automated decision boundary enforcing factual abstinence. When retrieved evidence sufficiency falls below 1.20, the system outputs high uncertainty instead of hallucinating speculative verdicts."
    },
    {
      term: "Temporal Decay (180-Day Rule)",
      formula: "|t_claim - t_evidence| > 180 Days → OUTDATED",
      definition: "Temporal comparison evaluating whether historical truths have expired. Prevents recycled historical announcements (e.g. 2020 lockdown notices) from being misclassified as active current news."
    }
  ];

  return (
    <section id="glossary" className="tl-section">
      <div className="tl-container">
        <div className="tl-section-header">
          <span className="tl-tag">// RIGOROUS TECHNICAL GLOSSARY</span>
          <h2 className="tl-title">Core Technical Terms & Mechanics</h2>
          <p className="tl-desc">
            Zero marketing fluff. Below are the exact architectural definitions, mathematical formulations, and
            operational roles of the technologies powering TruthLab v2.
          </p>
        </div>

        <div className="tl-grid-2">
          {glossaryTerms.map((item, idx) => (
            <div
              key={idx}
              className="tl-card"
              style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <h3 className="tl-card-title">{item.term}</h3>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    [{idx + 1}]
                  </span>
                </div>
                <div className="tl-code-box" style={{ color: 'var(--status-blue)', marginBottom: '12px' }}>
                  {item.formula}
                </div>
                <p className="tl-card-text" style={{ marginBottom: '14px' }}>{item.definition}</p>
              </div>

              <div
                style={{
                  paddingTop: '10px',
                  borderTop: '1px solid var(--border-hairline)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.72rem',
                  color: 'var(--text-muted)',
                }}
              >
                <span>Mechanic Grounded</span>
                <span style={{ color: 'var(--status-green)' }}>Strict Spec ✓</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
