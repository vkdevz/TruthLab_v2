import React from 'react';

export const ArchitectureSection: React.FC = () => {
  const steps = [
    {
      step: "01",
      title: "Input & Security Shield",
      desc: "Validates media headers via magic-byte inspection (JPEG, PNG, MP4, WebM) and filters URLs through socket-level DNS resolution to block private IP spaces and internal SSRF attacks."
    },
    {
      step: "02",
      title: "Signal Decomposition",
      desc: "Demuxes audio streams to 16kHz PCM WAV for Whisper speech recognition. Runs keyframe OCR and Error Level Analysis (ELA) at Q=90 to identify localized compression anomalies."
    },
    {
      step: "03",
      title: "Evidence Retrieval",
      desc: "Executes lexical BM25 and semantic cosine reranking against offline ClaimReview databases, live Wikipedia summaries, and verified journalistic repositories."
    },
    {
      step: "04",
      title: "Calibrated Adjudication",
      desc: "Natural Language Inference classifies evidence stance (Supports, Refutes, Neutral). Temperature scaling (T = 1.85) optimizes calibration, lowering Expected Calibration Error to 0.048."
    }
  ];

  return (
    <section id="architecture" className="m-section">
      <div className="m-container">
        <div className="m-section-label">System Flow</div>
        <h2 className="m-section-title">Verification Pipeline</h2>
        <p className="m-section-sub">
          A four-stage asynchronous pipeline combining signal processing, external evidentiary grounding, and mathematical logit calibration.
        </p>

        <div className="m-grid-4">
          {steps.map((s) => (
            <div key={s.step} className="m-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--text-faint)', marginBottom: '16px' }}>
                  {s.step}
                </div>
                <h3 className="m-card-title">{s.title}</h3>
                <p className="m-card-desc">{s.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
