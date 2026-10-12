import { useState, useEffect } from 'react';
import type { 
  VeracityLabel, 
  ClaimVerificationResult,
  ImageForensicIndicators,
  VideoForensicIndicators,
  FullVerificationResponse,
  EvidenceGraph
} from './types/verification';
import { EvidenceGraphView } from './components/EvidenceGraphView';
import { Navbar } from './components/Navbar';
import { ArchitectureSection } from './components/ArchitectureSection';
import { ForensicsDeepDive } from './components/ForensicsDeepDive';
import { ResearchBenchmarkTable } from './components/ResearchBenchmarkTable';
import { TechnicalGlossary } from './components/TechnicalGlossary';
import { Footer } from './components/Footer';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

interface BenchmarkSample {
  title: string;
  modality: 'TEXT' | 'URL' | 'IMAGE' | 'VIDEO';
  payload: string;
  expected: string;
}

const BENCHMARK_PRESETS: BenchmarkSample[] = [
  {
    title: "India 5G Ban Hoax",
    modality: "TEXT",
    payload: "The Indian Ministry of Communications has officially banned all 5G network services nationwide.",
    expected: "CONTRADICTED"
  },
  {
    title: "James Webb Discovery",
    modality: "TEXT",
    payload: "NASA's James Webb Space Telescope confirmed detection of atmospheric carbon dioxide on exoplanet WASP-39b.",
    expected: "SUPPORTED"
  },
  {
    title: "2020 Recycled Curfew",
    modality: "TEXT",
    payload: "Breaking right now: Curfew announced across the entire state due to health emergency!",
    expected: "OUTDATED"
  },
  {
    title: "Unindexed Rumor",
    modality: "TEXT",
    payload: "My local neighbor's cousin invented an invisible flying bicycle last night in his garage.",
    expected: "INSUFFICIENT_EVIDENCE"
  },
  {
    title: "Article URL (Anti-SSRF)",
    modality: "URL",
    payload: "https://en.wikipedia.org/wiki/James_Webb_Space_Telescope",
    expected: "SUPPORTED"
  },
  {
    title: "Image Meme (5G Hoax)",
    modality: "IMAGE",
    payload: "/samples/sample_5g_meme.png",
    expected: "CONTRADICTED"
  },
  {
    title: "Video Clip Sample",
    modality: "VIDEO",
    payload: "/samples/sample_news_clip.mp4",
    expected: "INSUFFICIENT_EVIDENCE"
  }
];

export function App() {
  const [activeTab, setActiveTab] = useState<'TEXT' | 'URL' | 'IMAGE' | 'VIDEO'>('TEXT');
  const [inputText, setInputText] = useState('');
  const [inputUrl, setInputUrl] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [filePreviewUrl, setFilePreviewUrl] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progressStage, setProgressStage] = useState('');
  const [activeClaimIdx, setActiveClaimIdx] = useState(0);

  // Result States
  const [overallVerdict, setOverallVerdict] = useState<VeracityLabel | null>(null);
  const [overallConfidence, setOverallConfidence] = useState<number>(0);
  const [uncertaintyLevel, setUncertaintyLevel] = useState<'LOW' | 'MODERATE' | 'HIGH' | null>(null);
  const [uncertaintyScore, setUncertaintyScore] = useState<number | null>(null);
  const [isActionable, setIsActionable] = useState<boolean | null>(null);
  const [evidenceFilter, setEvidenceFilter] = useState<'ALL' | 'SUPPORTS' | 'REFUTES' | 'NEUTRAL'>('ALL');
  const [verifiedClaims, setVerifiedClaims] = useState<ClaimVerificationResult[]>([]);
  const [imageForensics, setImageForensics] = useState<ImageForensicIndicators | null>(null);
  const [videoForensics, setVideoForensics] = useState<VideoForensicIndicators | null>(null);
  const [ocrText, setOcrText] = useState<string | null>(null);
  const [transcriptText, setTranscriptText] = useState<string | null>(null);
  const [executiveSummary, setExecutiveSummary] = useState<string>('');
  const [limitations, setLimitations] = useState<string[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [evidenceGraph, setEvidenceGraph] = useState<EvidenceGraph | null>(null);
  const [viewMode, setViewMode] = useState<'LIST' | 'GRAPH'>('GRAPH');

  // Clean up object URLs to prevent memory leaks
  useEffect(() => {
    if (selectedFile) {
      const objectUrl = URL.createObjectURL(selectedFile);
      setFilePreviewUrl(objectUrl);
      return () => URL.revokeObjectURL(objectUrl);
    } else {
      setFilePreviewUrl(null);
    }
  }, [selectedFile]);

  const handlePresetSelect = async (preset: BenchmarkSample) => {
    setActiveTab(preset.modality);
    setErrorMsg(null);
    if (preset.modality === 'URL') {
      setInputUrl(preset.payload);
      setSelectedFile(null);
    } else if (preset.modality === 'TEXT') {
      setInputText(preset.payload);
      setSelectedFile(null);
    } else if (preset.modality === 'IMAGE' || preset.modality === 'VIDEO') {
      try {
        const response = await fetch(preset.payload);
        const blob = await response.blob();
        const filename = preset.payload.split('/').pop() || 'sample_media';
        const mimeType = preset.modality === 'IMAGE' ? 'image/png' : 'video/mp4';
        const file = new File([blob], filename, { type: blob.type || mimeType });
        setSelectedFile(file);
      } catch (err) {
        console.error('Failed to load preset sample media:', err);
      }
    }
  };

  const applyVerificationResponse = (data: FullVerificationResponse) => {
    setVerifiedClaims(data.claims_verified || []);
    setOverallVerdict(data.overall_veracity);
    setOverallConfidence(data.overall_confidence);
    setUncertaintyLevel(data.uncertainty_level || 'LOW');
    setUncertaintyScore(data.uncertainty_score ?? 0.15);
    setIsActionable(data.is_actionable ?? true);
    setExecutiveSummary(data.executive_summary);
    setLimitations(data.system_limitations || []);
    setImageForensics(data.image_forensics || null);
    setVideoForensics(data.video_forensics || null);
    setOcrText(data.ocr_text || null);
    setTranscriptText(data.transcript_text || null);
    setEvidenceGraph(data.evidence_graph || null);
    setViewMode(data.evidence_graph && data.evidence_graph.nodes.length > 0 ? 'GRAPH' : 'LIST');
    setActiveClaimIdx(0);
    setEvidenceFilter('ALL');
  };

  const handleVerify = async () => {
    setErrorMsg(null);
    setIsProcessing(true);
    setProgressStage('Uploading and validating input...');

    try {
      if (activeTab === 'TEXT') {
        if (!inputText.trim()) {
          throw new Error('Please enter text to verify.');
        }

        setProgressStage('Decomposing claims & querying evidence indices...');
        const res = await fetch(`${API_BASE_URL}/api/v1/verify/text`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: inputText.trim() }),
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || 'Verification service error.');
        }

        const data: FullVerificationResponse = await res.json();
        applyVerificationResponse(data);
      } else if (activeTab === 'URL') {
        if (!inputUrl.trim()) {
          throw new Error('Please enter a valid HTTP/HTTPS article URL to verify.');
        }

        setProgressStage('Validating Anti-SSRF constraints & fetching article content...');
        const res = await fetch(`${API_BASE_URL}/api/v1/verify/url`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: inputUrl.trim() }),
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || 'URL verification failed.');
        }

        const data: FullVerificationResponse = await res.json();
        applyVerificationResponse(data);
      } else if (activeTab === 'IMAGE') {
        if (!selectedFile) {
          throw new Error('Please select an image file to upload.');
        }
        setProgressStage('Running OCR & visual forensics (ELA + synthetic indicator)...');

        const formData = new FormData();
        formData.append('file', selectedFile);

        const res = await fetch(`${API_BASE_URL}/api/v1/verify/image`, {
          method: 'POST',
          body: formData,
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || 'Image verification failed.');
        }

        const data: FullVerificationResponse = await res.json();
        applyVerificationResponse(data);
      } else if (activeTab === 'VIDEO') {
        if (!selectedFile) {
          throw new Error('Please select a video file to upload.');
        }
        setProgressStage('Probing video streams, sampling keyframes & extracting audio...');

        const formData = new FormData();
        formData.append('file', selectedFile);

        const res = await fetch(`${API_BASE_URL}/api/v1/verify/video`, {
          method: 'POST',
          body: formData,
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || 'Video verification failed.');
        }

        const data: FullVerificationResponse = await res.json();
        applyVerificationResponse(data);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Verification pipeline encountered an error.');
    } finally {
      setIsProcessing(false);
      setProgressStage('');
    }
  };

  const getVerdictStyle = (v: VeracityLabel | null) => {
    switch (v) {
      case 'SUPPORTED':
        return {
          color: 'var(--veracity-supported)',
          bg: 'var(--veracity-supported-bg)',
          border: 'var(--veracity-supported-border)',
        };
      case 'CONTRADICTED':
        return {
          color: 'var(--veracity-contradicted)',
          bg: 'var(--veracity-contradicted-bg)',
          border: 'var(--veracity-contradicted-border)',
        };
      case 'MISLEADING':
        return {
          color: 'var(--veracity-misleading)',
          bg: 'var(--veracity-misleading-bg)',
          border: 'var(--veracity-misleading-border)',
        };
      case 'OUTDATED':
        return {
          color: 'var(--veracity-outdated)',
          bg: 'var(--veracity-outdated-bg)',
          border: 'var(--veracity-outdated-border)',
        };
      default:
        return {
          color: 'var(--veracity-insufficient)',
          bg: 'var(--veracity-insufficient-bg)',
          border: 'var(--veracity-insufficient-border)',
        };
    }
  };

  const currentClaim = verifiedClaims[activeClaimIdx] || null;
  const vStyle = getVerdictStyle(overallVerdict);

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)', color: 'var(--text-main)' }}>
      <Navbar />

      <div id="workbench" className="tl-container" style={{ padding: '40px 24px' }}>
        {/* Header */}
        <header style={{ marginBottom: '28px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '3px 10px', borderRadius: 'var(--radius-sm)', background: 'var(--status-blue-bg)', border: '1px solid var(--status-blue-border)', marginBottom: '12px' }}>
              <span className="tl-pulse-dot" style={{ background: 'var(--status-blue)' }}></span>
              <span style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--status-blue)', fontFamily: 'var(--font-mono)' }}>
                RESEARCH ADJUDICATION TERMINAL
              </span>
            </div>
            <h1 style={{ fontSize: '2rem', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--text-primary)', marginBottom: '6px' }}>
              Multimodal Misinformation Verification System
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', maxWidth: '780px', lineHeight: 1.5 }}>
              Unified evidentiary reasoning across Plain Text, Article URLs, Screenshots, Memes, and Video Media.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <div className="tl-card" style={{ padding: '8px 14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="tl-pulse-dot"></span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>Engine Active :1234</span>
            </div>
          </div>
        </header>

        {/* Benchmark Presets Toolbar */}
        <section style={{ marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontWeight: 600, letterSpacing: '0.04em' }}>
              PRESETS:
            </span>
          {BENCHMARK_PRESETS.map((p, idx) => (
            <button
              key={idx}
              onClick={() => handlePresetSelect(p)}
              style={{
                background: 'rgba(255, 255, 255, 0.04)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-main)',
                padding: '6px 14px',
                borderRadius: '8px',
                fontSize: '0.85rem',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--accent-cyan)')}
              onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-subtle)')}
            >
              {p.title}
            </button>
          ))}
        </div>
      </section>

      {/* Main Ingestion & Verification Card */}
      <main className="glass-panel" style={{ padding: '28px', marginBottom: '32px' }}>
        {/* Modality Tabs */}
        <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '16px', marginBottom: '20px' }}>
          {(['TEXT', 'URL', 'IMAGE', 'VIDEO'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => {
                setActiveTab(tab);
                setErrorMsg(null);
              }}
              style={{
                background: activeTab === tab ? 'linear-gradient(135deg, var(--accent-indigo), var(--accent-violet))' : 'transparent',
                color: activeTab === tab ? '#fff' : 'var(--text-muted)',
                border: 'none',
                padding: '10px 20px',
                borderRadius: '8px',
                fontWeight: 600,
                fontSize: '0.9rem',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
            >
              {tab === 'TEXT' ? 'Plain Text / Claim' : tab === 'URL' ? 'Article URL (Anti-SSRF)' : tab === 'IMAGE' ? 'Image / Screenshot / Meme' : 'Video / Clip'}
            </button>
          ))}
        </div>

        {/* Input Controls */}
        {activeTab === 'TEXT' ? (
          <div>
            <textarea
              rows={4}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Enter factual claim or news passage to verify (e.g. 'NASA scientists officially confirmed alien signals received today')..."
              style={{
                width: '100%',
                background: 'rgba(10, 13, 20, 0.8)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '10px',
                color: 'var(--text-main)',
                padding: '14px',
                fontSize: '0.95rem',
                fontFamily: 'var(--font-sans)',
                outline: 'none',
                resize: 'vertical',
              }}
            />
          </div>
        ) : activeTab === 'URL' ? (
          <div>
            <input
              type="url"
              value={inputUrl}
              onChange={(e) => setInputUrl(e.target.value)}
              placeholder="https://news.example.com/article-to-verify"
              style={{
                width: '100%',
                background: 'rgba(10, 13, 20, 0.8)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '10px',
                color: 'var(--text-main)',
                padding: '14px',
                fontSize: '0.95rem',
                fontFamily: 'var(--font-sans)',
                outline: 'none',
              }}
            />
            <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginTop: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span>🛡️</span> Protected by Anti-SSRF (DNS resolution, private CIDR filtering, redirect cap, 5MB response limit).
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{
              border: '2px dashed var(--border-subtle)',
              borderRadius: '12px',
              padding: '32px',
              textAlign: 'center',
              background: 'rgba(10, 13, 20, 0.4)',
            }}>
              <input
                type="file"
                accept={activeTab === 'IMAGE' ? 'image/*' : 'video/*'}
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                id="file-upload"
                style={{ display: 'none' }}
              />
              <label htmlFor="file-upload" style={{ cursor: 'pointer' }}>
                <div style={{ fontSize: '2rem', marginBottom: '8px' }}>
                  {activeTab === 'IMAGE' ? '🖼️' : '🎬'}
                </div>
                <div style={{ fontWeight: 600, fontSize: '1rem', color: 'var(--accent-cyan)' }}>
                  {selectedFile ? selectedFile.name : `Click to choose ${activeTab.toLowerCase()} file`}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginTop: '4px' }}>
                  {activeTab === 'IMAGE' ? 'Supported: PNG, JPEG, WEBP, BMP (Max 15MB)' : 'Supported: MP4, MOV, WEBM (Max 60MB, duration <= 90s)'}
                </div>
              </label>
            </div>

            {/* Media Preview Box */}
            {filePreviewUrl && (
              <div style={{ display: 'flex', justifyContent: 'center', background: 'rgba(0,0,0,0.4)', padding: '16px', borderRadius: '10px' }}>
                {activeTab === 'IMAGE' ? (
                  <img
                    src={filePreviewUrl}
                    alt="Upload Preview"
                    style={{ maxHeight: '240px', maxWidth: '100%', objectFit: 'contain', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}
                  />
                ) : (
                  <video
                    src={filePreviewUrl}
                    controls
                    style={{ maxHeight: '240px', maxWidth: '100%', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}
                  />
                )}
              </div>
            )}
          </div>
        )}

        {/* Action Button & Stepper */}
        <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            {isProcessing && (
              <span style={{ fontSize: '0.9rem', color: 'var(--accent-cyan)', display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                <span className="pulsing-glow">⚡</span> {progressStage}
              </span>
            )}
            {errorMsg && (
              <span style={{ fontSize: '0.9rem', color: 'var(--veracity-contradicted)' }}>
                ⚠️ {errorMsg}
              </span>
            )}
          </div>

          <button
            onClick={handleVerify}
            disabled={isProcessing}
            style={{
              background: 'linear-gradient(135deg, #38bdf8 0%, #6366f1 100%)',
              color: '#fff',
              border: 'none',
              padding: '12px 28px',
              borderRadius: '10px',
              fontWeight: 700,
              fontSize: '0.95rem',
              cursor: isProcessing ? 'not-allowed' : 'pointer',
              opacity: isProcessing ? 0.7 : 1,
              boxShadow: 'var(--shadow-glow)',
              transition: 'all 0.2s',
            }}
          >
            {isProcessing ? 'Verifying...' : `Verify ${activeTab === 'TEXT' ? 'Text' : activeTab === 'URL' ? 'URL' : activeTab}`}
          </button>
        </div>
      </main>

      {/* Results View */}
      {overallVerdict && (
        <section style={{ animation: 'fadeIn 0.3s ease-in-out' }}>
          {/* Scientific Epistemic Humility Banner */}
          <div
            style={{
              background: 'rgba(56, 189, 248, 0.06)',
              border: '1px solid rgba(56, 189, 248, 0.25)',
              borderRadius: '10px',
              padding: '12px 18px',
              marginBottom: '20px',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              fontSize: '0.85rem',
              color: 'var(--text-main)',
            }}
          >
            <span style={{ fontSize: '1.25rem' }}>🛡️</span>
            <div>
              <strong style={{ color: 'var(--accent-cyan)' }}>Operational Notice:</strong> This system assists empirical verification by synthesizing observable evidentiary citations, temporal anchors, and media forensic signals; <em>it does not possess an infallible truth oracle</em>. Decisions should be corroborated before high-stakes distribution.
            </div>
          </div>

          {/* Verdict Banner */}
          <div
            className="glass-panel"
            style={{
              padding: '28px',
              borderLeft: `6px solid ${vStyle.color}`,
              background: vStyle.bg,
              marginBottom: '24px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '16px',
            }}
          >
            <div>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, color: vStyle.color, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                Overall Verification Assessment
              </div>
              <div style={{ fontSize: '2.4rem', fontWeight: 800, color: vStyle.color, letterSpacing: '-0.02em', marginTop: '4px' }}>
                {overallVerdict}
              </div>
              <p style={{ marginTop: '8px', fontSize: '1rem', color: 'var(--text-main)', maxWidth: '780px' }}>
                {executiveSummary}
              </p>
              {limitations.length > 0 && (
                <div style={{ marginTop: '12px', fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                  ⚠️ System limitations: {limitations.join(' • ')}
                </div>
              )}
            </div>

            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Calibrated Confidence</div>
              <div style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--text-main)', fontFamily: 'var(--font-mono)' }}>
                {(overallConfidence * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Temperature / Platt Scaled</div>
            </div>

            {/* Uncertainty and Calibration Telemetry */}
            <div
              style={{
                width: '100%',
                marginTop: '16px',
                paddingTop: '16px',
                borderTop: '1px solid rgba(255, 255, 255, 0.08)',
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '16px',
              }}
            >
              <div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.05em' }}>
                  Uncertainty Estimation
                </div>
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                  <span
                    style={{
                      padding: '3px 10px',
                      borderRadius: '999px',
                      fontSize: '0.78rem',
                      fontWeight: 700,
                      background: uncertaintyLevel === 'LOW' ? 'rgba(16, 185, 129, 0.18)' : uncertaintyLevel === 'HIGH' ? 'rgba(239, 68, 68, 0.18)' : 'rgba(245, 158, 11, 0.18)',
                      color: uncertaintyLevel === 'LOW' ? '#10b981' : uncertaintyLevel === 'HIGH' ? '#ef4444' : '#f59e0b',
                      border: `1px solid ${uncertaintyLevel === 'LOW' ? 'rgba(16, 185, 129, 0.35)' : uncertaintyLevel === 'HIGH' ? 'rgba(239, 68, 68, 0.35)' : 'rgba(245, 158, 11, 0.35)'}`,
                    }}
                  >
                    {uncertaintyLevel || 'LOW'} UNCERTAINTY
                  </span>
                  {uncertaintyScore !== null && (
                    <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      (Score: {uncertaintyScore.toFixed(2)})
                    </span>
                  )}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.05em' }}>
                  Actionability Assessment
                </div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, marginTop: '4px', color: isActionable !== false ? '#10b981' : '#f59e0b' }}>
                  {isActionable !== false ? '✅ Actionable Decision' : '⚠️ Elevated Ambiguity (Review Suggested)'}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.05em' }}>
                  Reliability Model
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Calibrated Platt / Temperature Scaling
                </div>
              </div>
            </div>
          </div>

          {/* Extracted Modality Findings Strip */}
          {(ocrText || transcriptText) && (
            <div className="glass-panel" style={{ padding: '20px', marginBottom: '24px', background: 'rgba(255, 255, 255, 0.02)' }}>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--accent-cyan)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '10px' }}>
                Extracted Textual Corpus (Grounding Claims)
              </h4>
              {ocrText && (
                <div style={{ marginBottom: transcriptText ? '12px' : '0' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)', fontWeight: 600 }}>OCR Text Detected in Media: </span>
                  <span style={{ fontSize: '0.9rem', color: 'var(--text-main)' }}>"{ocrText}"</span>
                </div>
              )}
              {transcriptText && (
                <div>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)', fontWeight: 600 }}>ASR Speech Transcript: </span>
                  <span style={{ fontSize: '0.9rem', color: 'var(--text-main)' }}>"{transcriptText}"</span>
                </div>
              )}
            </div>
          )}

          {/* Grid Layout: Claims & Evidence (Left) + Forensics (Right) */}
          <div style={{ display: 'grid', gridTemplateColumns: imageForensics || videoForensics ? '2fr 1.1fr' : '1fr', gap: '24px' }}>
            {/* Left Column: Claims & Evidence */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
                <h3 style={{ fontSize: '1.2rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                  <span>🔍</span> Factual Evidence Verification
                </h3>
                <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
                  <div style={{ display: 'inline-flex', background: 'rgba(255, 255, 255, 0.06)', borderRadius: '6px', padding: '3px', border: '1px solid var(--border-subtle)' }}>
                    <button
                      onClick={() => setViewMode('GRAPH')}
                      style={{
                        background: viewMode === 'GRAPH' ? 'linear-gradient(135deg, var(--accent-indigo), var(--accent-violet))' : 'transparent',
                        color: viewMode === 'GRAPH' ? '#fff' : 'var(--text-muted)',
                        border: 'none',
                        padding: '4px 10px',
                        borderRadius: '4px',
                        fontSize: '0.78rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        transition: 'all 0.15s',
                      }}
                    >
                      🕸️ Evidence Graph
                    </button>
                    <button
                      onClick={() => setViewMode('LIST')}
                      style={{
                        background: viewMode === 'LIST' ? 'linear-gradient(135deg, var(--accent-indigo), var(--accent-violet))' : 'transparent',
                        color: viewMode === 'LIST' ? '#fff' : 'var(--text-muted)',
                        border: 'none',
                        padding: '4px 10px',
                        borderRadius: '4px',
                        fontSize: '0.78rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        transition: 'all 0.15s',
                      }}
                    >
                      📄 Citations List
                    </button>
                  </div>
                  <span style={{ fontSize: '0.75rem', padding: '3px 8px', borderRadius: '4px', background: 'rgba(56, 189, 248, 0.1)', color: 'var(--accent-cyan)', border: '1px solid rgba(56, 189, 248, 0.25)' }}>
                    Ground Truth Indices
                  </span>
                </div>
              </div>

              {verifiedClaims.length > 0 ? (
                <div>
                  {/* Claim Selector Pills */}
                  {verifiedClaims.length > 1 && (
                    <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', overflowX: 'auto', paddingBottom: '4px' }}>
                      {verifiedClaims.map((_, idx) => (
                        <button
                          key={idx}
                          onClick={() => setActiveClaimIdx(idx)}
                          style={{
                            background: activeClaimIdx === idx ? 'var(--bg-tertiary)' : 'rgba(255, 255, 255, 0.05)',
                            border: `1px solid ${activeClaimIdx === idx ? 'var(--accent-cyan)' : 'var(--border-subtle)'}`,
                            color: 'var(--text-main)',
                            padding: '6px 14px',
                            borderRadius: '6px',
                            fontSize: '0.85rem',
                            cursor: 'pointer',
                          }}
                        >
                          Claim #{idx + 1}
                        </button>
                      ))}
                    </div>
                  )}

                  {currentClaim && (
                    <div>
                      <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '16px', borderRadius: '8px', marginBottom: '20px' }}>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>Target Proposition</div>
                        <div style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-main)', marginTop: '4px' }}>
                          "{currentClaim.claim.canonical_claim}"
                        </div>
                        <div style={{ display: 'flex', gap: '12px', marginTop: '10px', fontSize: '0.8rem', color: 'var(--text-muted)', flexWrap: 'wrap' }}>
                          <span>Check-worthiness: {(currentClaim.claim.checkworthy_score * 100).toFixed(0)}%</span>
                          <span>•</span>
                          <span>Sufficiency Index: {currentClaim.evidence_sufficiency_score.toFixed(2)}</span>
                          {currentClaim.is_temporal_mismatch && (
                            <>
                              <span>•</span>
                              <span style={{ color: 'var(--veracity-outdated)', fontWeight: 600 }}>Temporal Delta Detected</span>
                            </>
                          )}
                        </div>
                      </div>

                      {/* Interactive Graph View Rendering */}
                      {viewMode === 'GRAPH' && evidenceGraph && (
                        <div style={{ marginBottom: '20px' }}>
                          <EvidenceGraphView
                            graph={evidenceGraph}
                            overallVerdict={overallVerdict}
                            onSelectCitation={() => setViewMode('LIST')}
                          />
                        </div>
                      )}

                      {/* Evidence Citations Header & Stance Filters */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '14px' }}>
                        <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', margin: 0 }}>
                          Verified Citations & Stance Records ({currentClaim.evidence_items.length})
                        </h4>

                        {/* Stance Filter Buttons */}
                        <div style={{ display: 'flex', gap: '6px' }}>
                          {(['ALL', 'SUPPORTS', 'REFUTES', 'NEUTRAL'] as const).map((filter) => {
                            const count = filter === 'ALL'
                              ? currentClaim.evidence_items.length
                              : currentClaim.evidence_items.filter(e => e.stance === filter).length;
                            return (
                              <button
                                key={filter}
                                onClick={() => setEvidenceFilter(filter)}
                                style={{
                                  background: evidenceFilter === filter ? 'rgba(56, 189, 248, 0.15)' : 'rgba(255, 255, 255, 0.04)',
                                  border: `1px solid ${evidenceFilter === filter ? 'var(--accent-cyan)' : 'var(--border-subtle)'}`,
                                  color: evidenceFilter === filter ? 'var(--accent-cyan)' : 'var(--text-dim)',
                                  padding: '4px 10px',
                                  borderRadius: '6px',
                                  fontSize: '0.75rem',
                                  fontWeight: 600,
                                  cursor: 'pointer',
                                }}
                              >
                                {filter === 'ALL' ? 'All' : filter === 'SUPPORTS' ? 'Supports' : filter === 'REFUTES' ? 'Refutes' : 'Neutral'} ({count})
                              </button>
                            );
                          })}
                        </div>
                      </div>

                      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        {currentClaim.evidence_items
                          .filter(ev => evidenceFilter === 'ALL' || ev.stance === evidenceFilter)
                          .map((ev, eIdx) => {
                          const isRefute = ev.stance === 'REFUTES';
                          const isSupp = ev.stance === 'SUPPORTS';
                          return (
                            <div
                              key={eIdx}
                              style={{
                                background: 'rgba(255, 255, 255, 0.02)',
                                border: '1px solid var(--border-subtle)',
                                borderRadius: '8px',
                                padding: '14px',
                              }}
                            >
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                  <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-main)' }}>{ev.source_name}</span>
                                  <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '4px', background: 'rgba(255, 255, 255, 0.08)', color: 'var(--text-dim)' }}>
                                    Weight: {ev.domain_credibility_weight}x
                                  </span>
                                </div>
                                <span
                                  style={{
                                    fontSize: '0.75rem',
                                    fontWeight: 700,
                                    padding: '2px 8px',
                                    borderRadius: '4px',
                                    background: isRefute ? 'rgba(239, 68, 68, 0.2)' : isSupp ? 'rgba(16, 185, 129, 0.2)' : 'rgba(100, 116, 139, 0.2)',
                                    color: isRefute ? '#ef4444' : isSupp ? '#10b981' : '#94a3b8',
                                  }}
                                >
                                  {ev.stance}
                                </span>
                              </div>
                              <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                                "{ev.snippet_text}"
                              </p>

                              {/* Probabilistic Stance Distribution Bar */}
                              {ev.stance_probabilities && (
                                <div style={{ marginTop: '8px', display: 'flex', gap: '8px', alignItems: 'center', fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                                  <span>NLI Marginals:</span>
                                  <span style={{ color: '#10b981' }}>Supp: {(ev.stance_probabilities.SUPPORTS * 100).toFixed(0)}%</span>
                                  <span>•</span>
                                  <span style={{ color: '#ef4444' }}>Ref: {(ev.stance_probabilities.REFUTES * 100).toFixed(0)}%</span>
                                  <span>•</span>
                                  <span style={{ color: '#94a3b8' }}>Neut: {(ev.stance_probabilities.NEUTRAL * 100).toFixed(0)}%</span>
                                </div>
                              )}
                              <div style={{ marginTop: '8px' }}>
                                <a
                                  href={ev.source_url}
                                  target="_blank"
                                  rel="noreferrer"
                                  style={{ color: 'var(--accent-cyan)', fontSize: '0.8rem', textDecoration: 'none' }}
                                >
                                  🔗 Direct Source Citation ({ev.domain})
                                </a>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ color: 'var(--text-dim)', fontSize: '0.9rem', padding: '16px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
                  No check-worthy propositional claims were extracted from this media input. The verdict reflects empirical insufficiency.
                </div>
              )}
            </div>

            {/* Right Column: Media Forensics */}
            {(imageForensics || videoForensics) && (
              <div className="glass-panel" style={{ padding: '24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span>🛡️</span> Media Forensic Signals
                  </h3>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '16px' }}>
                  * Probabilistic heuristics only — not binary or definitive proof of tampering.
                </div>

                {imageForensics && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div style={{ background: 'rgba(0,0,0,0.3)', padding: '14px', borderRadius: '8px' }}>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Probabilistic AI-Generation Indicator</div>
                      <div style={{ fontSize: '1.6rem', fontWeight: 800, color: imageForensics.synthetic_probability > 0.6 ? '#f59e0b' : '#10b981', fontFamily: 'var(--font-mono)' }}>
                        {(imageForensics.synthetic_probability * 100).toFixed(0)}%
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Calibrated Confidence: {imageForensics.synthetic_confidence}</div>
                    </div>

                    <div style={{ background: 'rgba(0,0,0,0.3)', padding: '14px', borderRadius: '8px' }}>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Error Level Analysis (ELA)</div>
                      <div style={{ fontSize: '1.05rem', fontWeight: 700, marginTop: '2px', color: imageForensics.is_ela_spliced ? '#ef4444' : '#10b981' }}>
                        {imageForensics.is_ela_spliced ? 'Localized Compression Splicing' : 'Uniform Compression'}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Max Error Level: {imageForensics.ela_max_error}</div>
                    </div>

                    <div style={{ background: 'rgba(0,0,0,0.3)', padding: '14px', borderRadius: '8px' }}>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Provenance & C2PA Credentials</div>
                      <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-main)', marginTop: '2px' }}>
                        {imageForensics.c2pa_present ? '✅ C2PA Manifest Present' : 'Standard Metadata (No C2PA Manifest)'}
                      </div>
                      {imageForensics.software_tag && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)', marginTop: '2px' }}>
                          Editor Tag: {imageForensics.software_tag}
                        </div>
                      )}
                    </div>

                    {imageForensics.forensic_notes.length > 0 && (
                      <div>
                        <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '6px' }}>
                          Forensic Observations:
                        </div>
                        <ul style={{ paddingLeft: '16px', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                          {imageForensics.forensic_notes.map((n, idx) => (
                            <li key={idx} style={{ marginBottom: '4px' }}>{n}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {videoForensics && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div style={{ background: 'rgba(0,0,0,0.3)', padding: '14px', borderRadius: '8px' }}>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Sampled Keyframe Synthetic Metric</div>
                      <div style={{ fontSize: '1.6rem', fontWeight: 800, color: (videoForensics.synthetic_face_probability || 0.15) > 0.6 ? '#f59e0b' : '#10b981', fontFamily: 'var(--font-mono)' }}>
                        {(((videoForensics.synthetic_face_probability || 0.15)) * 100).toFixed(0)}%
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>* Heuristic frequency inspection across keyframes</div>
                    </div>

                    <div style={{ background: 'rgba(0,0,0,0.3)', padding: '14px', borderRadius: '8px' }}>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Stream Diagnostics</div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-main)', marginTop: '4px' }}>
                        Duration: {videoForensics.duration_seconds.toFixed(1)}s • Scenes Sampled: {videoForensics.extracted_scenes}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                        Audio Track: {videoForensics.has_audio_track ? 'Detected' : 'Silent / None'}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </section>
      )}
      </div>

      <ArchitectureSection />
      <ForensicsDeepDive />
      <ResearchBenchmarkTable />
      <TechnicalGlossary />
      <Footer />
    </div>
  );
}
export default App;

