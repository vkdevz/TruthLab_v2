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
      latency: "3.2s / 10.4s",
      highlight: true
    }
  ];

  return (
    <section id="benchmarks" className="m-section">
      <div className="m-container">
        <div className="m-section-label">Empirical Evaluation</div>
        <h2 className="m-section-title">Benchmark Results</h2>
        <p className="m-section-sub">
          Evaluated across 15 structured experiments with McNemar exact testing and 1,000-sample bootstrap validation.
        </p>

        {/* Desktop View: Full Comparative Table */}
        <div className="m-desktop-only" style={{ border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', background: 'var(--bg-card)', overflowX: 'auto', marginBottom: '28px' }}>
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
                <tr key={i} style={r.highlight ? { background: 'rgba(255, 255, 255, 0.025)' } : {}}>
                  <td style={{ fontFamily: 'var(--font-sans)', color: r.highlight ? 'var(--text-primary)' : 'var(--text-secondary)', fontWeight: r.highlight ? 600 : 400 }}>
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

        {/* Dedicated Mobile View: Stacked Benchmark Comparison Cards (No Horizontal Table Scroll) */}
        <div className="m-mobile-only" style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>
          {rows.map((r, i) => (
            <div
              key={i}
              className="m-card"
              style={{
                border: r.highlight ? '1px solid var(--border-focus)' : '1px solid var(--border-subtle)',
                padding: '16px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <div>
                  <div style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)' }}>{r.arch}</div>
                  <div style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>Modality: {r.modality}</div>
                </div>
                {r.highlight && (
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.68rem', padding: '2px 8px', borderRadius: '4px', background: 'var(--veracity-supported-bg)', color: 'var(--veracity-supported)', border: '1px solid var(--veracity-supported-border)' }}>
                    Primary
                  </span>
                )}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', background: 'var(--bg-input)', padding: '10px', borderRadius: 'var(--radius-sm)', fontFamily: 'var(--font-mono)' }}>
                <div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>ACC</div>
                  <div style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-primary)' }}>{r.accuracy}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>F1</div>
                  <div style={{ fontSize: '0.84rem', color: 'var(--text-secondary)' }}>{r.f1}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>ECE</div>
                  <div style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-primary)' }}>{r.eceCal}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>TIME</div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{r.latency}</div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* 3 Quiet Stat Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '14px' }}>
          <div className="m-card">
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
              Bootstrap Delta (1k)
            </div>
            <div style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
              +0.250 F1 Mean
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              Non-parametric resampling demonstrates consistent positive directional gain over baseline.
            </p>
          </div>

          <div className="m-card">
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
              Calibration (T = 1.85)
            </div>
            <div style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
              -73.6% ECE
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              Temperature scaling reduces Expected Calibration Error from 0.182 to 0.048.
            </p>
          </div>

          <div className="m-card">
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
              Regression Suite
            </div>
            <div style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
              137 / 137 Passing
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              Full unit, forensic, and security test coverage executing in 33 seconds.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};
