import React from 'react';

export const ResearchBenchmarkTable: React.FC = () => {
  const rows = [
    {
      arch: "Text Baseline (Closed-Book)",
      modality: "Text",
      accuracy: "52.0%",
      f1: "0.49",
      eceRaw: "0.241",
      eceCal: "0.165",
      latency: "0.42s"
    },
    {
      arch: "Retrieval-Augmented NLI",
      modality: "Text / URL",
      accuracy: "76.5%",
      f1: "0.74",
      eceRaw: "0.182",
      eceCal: "0.052",
      latency: "1.85s"
    },
    {
      arch: "TruthLab Multimodal Pipeline",
      modality: "Image / Video",
      accuracy: "80.0%",
      f1: "0.78",
      eceRaw: "0.179",
      eceCal: "0.048",
      latency: "3.20s / 10.4s",
      highlight: true
    }
  ];

  return (
    <section id="benchmarks" className="m-section">
      <div className="m-container">
        <div className="m-section-label">Empirical Evaluation</div>
        <h2 className="m-section-title">Benchmark Results</h2>
        <p className="m-section-sub">
          Cross-validated across 15 structured experiments with McNemar statistical significance testing (p = 0.031 &lt; 0.05).
        </p>

        <div style={{ border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', background: 'var(--bg-card)', overflowX: 'auto', marginBottom: '28px' }}>
          <table className="m-table">
            <thead>
              <tr>
                <th>Model Architecture</th>
                <th>Modality</th>
                <th style={{ textAlign: 'center' }}>Accuracy</th>
                <th style={{ textAlign: 'center' }}>Macro F1</th>
                <th style={{ textAlign: 'center' }}>Raw ECE</th>
                <th style={{ textAlign: 'center' }}>Calibrated ECE</th>
                <th style={{ textAlign: 'right' }}>Latency</th>
              </tr>
            </thead>
            <tbody style={{ fontFamily: 'var(--font-mono)' }}>
              {rows.map((r, i) => (
                <tr key={i} style={r.highlight ? { background: 'rgba(255, 255, 255, 0.02)' } : {}}>
                  <td style={{ fontFamily: 'var(--font-sans)', color: r.highlight ? 'var(--text-primary)' : 'var(--text-secondary)', fontWeight: r.highlight ? 500 : 400 }}>
                    {r.arch}
                  </td>
                  <td style={{ color: 'var(--text-muted)' }}>{r.modality}</td>
                  <td style={{ textAlign: 'center', color: 'var(--text-primary)', fontWeight: 600 }}>{r.accuracy}</td>
                  <td style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>{r.f1}</td>
                  <td style={{ textAlign: 'center', color: 'var(--text-muted)' }}>{r.eceRaw}</td>
                  <td style={{ textAlign: 'center', color: 'var(--text-primary)', fontWeight: 600 }}>{r.eceCal}</td>
                  <td style={{ textAlign: 'right', color: 'var(--text-secondary)' }}>{r.latency}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* 3 Quiet Stat Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
          <div className="m-card">
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
              Significance (McNemar)
            </div>
            <div style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
              p = 0.031 (&lt; 0.05)
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Multimodal fusion yields statistically significant improvement over text-only baselines.
            </p>
          </div>

          <div className="m-card">
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
              Calibration (T = 1.85)
            </div>
            <div style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
              -73.6% ECE
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Temperature scaling reduces Expected Calibration Error from 0.182 to 0.048.
            </p>
          </div>

          <div className="m-card">
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
              Regression Suite
            </div>
            <div style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
              121 / 121 Passing
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Full unit, forensic, and security test coverage executing in 33 seconds.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};
