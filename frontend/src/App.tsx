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
import { ResearchBenchmarkTable } from './components/ResearchBenchmarkTable';
import { MethodologySection } from './components/MethodologySection';
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
    title: "5G Ban Hoax",
    modality: "TEXT",
    payload: "The Indian Ministry of Communications has officially banned all 5G network services nationwide.",
    expected: "CONTRADICTED"
  },
  {
    title: "NASA Discovery",
    modality: "TEXT",
    payload: "NASA's James Webb Space Telescope confirmed detection of atmospheric carbon dioxide on exoplanet WASP-39b.",
    expected: "SUPPORTED"
  },
  {
    title: "2020 Curfew",
    modality: "TEXT",
    payload: "Breaking right now: Curfew announced across the entire state due to health emergency!",
    expected: "OUTDATED"
  },
  {
    title: "5G Meme Image",
    modality: "IMAGE",
    payload: "/samples/sample_5g_meme.png",
    expected: "CONTRADICTED"
  },
  {
    title: "Video News Clip",
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
  const [verifiedClaims, setVerifiedClaims] = useState<ClaimVerificationResult[]>([]);
  const [imageForensics, setImageForensics] = useState<ImageForensicIndicators | null>(null);
  const [videoForensics, setVideoForensics] = useState<VideoForensicIndicators | null>(null);
  const [ocrText, setOcrText] = useState<string | null>(null);
  const [transcriptText, setTranscriptText] = useState<string | null>(null);
  const [executiveSummary, setExecutiveSummary] = useState<string>('');
  const [limitations, setLimitations] = useState<string[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [evidenceGraph, setEvidenceGraph] = useState<EvidenceGraph | null>(null);
  const [viewMode, setViewMode] = useState<'GRAPH' | 'CITATIONS' | 'FORENSICS'>('GRAPH');

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
        console.error('Failed to load preset media:', err);
      }
    }
  };

  const applyVerificationResponse = (data: FullVerificationResponse) => {
    setVerifiedClaims(data.claims_verified || []);
    setOverallVerdict(data.overall_veracity);
    setOverallConfidence(data.overall_confidence);
    setUncertaintyLevel(data.uncertainty_level || 'LOW');
    setUncertaintyScore(data.uncertainty_score ?? 0.15);
    setExecutiveSummary(data.executive_summary);
    setLimitations(data.system_limitations || []);
    setImageForensics(data.image_forensics || null);
    setVideoForensics(data.video_forensics || null);
    setOcrText(data.ocr_text || null);
    setTranscriptText(data.transcript_text || null);
    setEvidenceGraph(data.evidence_graph || null);
    setViewMode(data.evidence_graph && data.evidence_graph.nodes.length > 0 ? 'GRAPH' : 'CITATIONS');
    setActiveClaimIdx(0);
  };

  const handleVerify = async () => {
    setErrorMsg(null);
    setIsProcessing(true);
    setProgressStage('Validating payload...');

    try {
      if (activeTab === 'TEXT') {
        if (!inputText.trim()) throw new Error('Please enter text to verify.');
        setProgressStage('Decomposing claims & searching evidence...');
        const res = await fetch(`${API_BASE_URL}/api/v1/verify/text`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: inputText.trim() }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || 'Text verification failed.');
        }
        applyVerificationResponse(await res.json());
      } else if (activeTab === 'URL') {
        if (!inputUrl.trim()) throw new Error('Please enter a URL to verify.');
        setProgressStage('Anti-SSRF validation & content extraction...');
        const res = await fetch(`${API_BASE_URL}/api/v1/verify/url`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: inputUrl.trim() }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || 'URL verification failed.');
        }
        applyVerificationResponse(await res.json());
      } else if (activeTab === 'IMAGE') {
        if (!selectedFile) throw new Error('Please select an image file.');
        setProgressStage('Executing OCR & ELA compression forensics...');
        const formData = new FormData();
        formData.append('file', selectedFile);
        const res = await fetch(`${API_BASE_URL}/api/v1/verify/image`, {
          method: 'POST',
          body: formData,
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || 'Image verification failed.');
        }
        applyVerificationResponse(await res.json());
      } else if (activeTab === 'VIDEO') {
        if (!selectedFile) throw new Error('Please select a video file.');
        setProgressStage('Probing video, demuxing audio & keyframe OCR...');
        const formData = new FormData();
        formData.append('file', selectedFile);
        const res = await fetch(`${API_BASE_URL}/api/v1/verify/video`, {
          method: 'POST',
          body: formData,
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || 'Video verification failed.');
        }
        applyVerificationResponse(await res.json());
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Verification failure.');
    } finally {
      setIsProcessing(false);
      setProgressStage('');
    }
  };

  const getVerdictTheme = (v: VeracityLabel | null) => {
    switch (v) {
      case 'SUPPORTED':
        return {
          color: 'var(--veracity-supported)',
          bg: 'var(--veracity-supported-bg)',
          border: 'var(--veracity-supported-border)',
          label: 'Supported'
        };
      case 'CONTRADICTED':
        return {
          color: 'var(--veracity-contradicted)',
          bg: 'var(--veracity-contradicted-bg)',
          border: 'var(--veracity-contradicted-border)',
          label: 'Contradicted'
        };
      case 'OUTDATED':
        return {
          color: 'var(--veracity-outdated)',
          bg: 'var(--veracity-outdated-bg)',
          border: 'var(--veracity-outdated-border)',
          label: 'Outdated'
        };
      default:
        return {
          color: 'var(--veracity-insufficient)',
          bg: 'var(--veracity-insufficient-bg)',
          border: 'var(--veracity-insufficient-border)',
          label: 'Insufficient Evidence'
        };
    }
  };

  const theme = getVerdictTheme(overallVerdict);
  const currentClaim = verifiedClaims[activeClaimIdx] || null;

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />

      {/* Hero Section */}
      <section className="m-hero">
        <div className="m-container">
          <div className="m-hero-pill">
            <span className="m-hero-dot"></span>
            <span>Multimodal Misinformation Verification Engine</span>
          </div>
          <h1 className="m-hero-title">Adjudicate Truth with Empirical Evidence</h1>
          <p className="m-hero-subtitle">
            Evidentiary reasoning and forensic signal extraction across Text, Article URLs, Images, and Video Media.
          </p>
        </div>
      </section>

      {/* Main Verification Workbench */}
      <main id="workbench" className="m-container" style={{ paddingBottom: '60px' }}>
        <div className="m-console-card">
          {/* Segmented Modality Selector */}
          <div className="m-tabs-wrap">
            <div className="m-tabs">
              {(['TEXT', 'URL', 'IMAGE', 'VIDEO'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => {
                    setActiveTab(tab);
                    setErrorMsg(null);
                  }}
                  className={`m-tab-btn ${activeTab === tab ? 'active' : ''}`}
                >
                  {tab === 'TEXT' ? 'Text' : tab === 'URL' ? 'URL' : tab === 'IMAGE' ? 'Image' : 'Video'}
                </button>
              ))}
            </div>
          </div>

          {/* Input Modality Form */}
          {activeTab === 'TEXT' ? (
            <div>
              <textarea
                rows={3}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Enter claim or passage to verify..."
                className="m-textarea"
              />
            </div>
          ) : activeTab === 'URL' ? (
            <div>
              <input
                type="url"
                value={inputUrl}
                onChange={(e) => setInputUrl(e.target.value)}
                placeholder="https://news.example.com/article-url"
                className="m-input-text"
              />
            </div>
          ) : (
            <div>
              <div
                className="m-dropzone"
                onClick={() => document.getElementById('file-upload-input')?.click()}
              >
                <input
                  type="file"
                  id="file-upload-input"
                  accept={activeTab === 'IMAGE' ? 'image/*' : 'video/*'}
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  style={{ display: 'none' }}
                />
                <div style={{ fontSize: '0.88rem', color: 'var(--text-primary)', fontWeight: 500, marginBottom: '4px' }}>
                  {selectedFile ? selectedFile.name : `Select ${activeTab.toLowerCase()} file`}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {activeTab === 'IMAGE' ? 'PNG, JPEG, WEBP (Max 15MB)' : 'MP4, MOV, WebM (Max 60MB, <= 90s)'}
                </div>
              </div>

              {/* Media Preview */}
              {filePreviewUrl && (
                <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'center', background: 'var(--bg-input)', padding: '16px', borderRadius: 'var(--radius-md)' }}>
                  {activeTab === 'IMAGE' ? (
                    <img
                      src={filePreviewUrl}
                      alt="Preview"
                      style={{ maxHeight: '200px', maxWidth: '100%', objectFit: 'contain', borderRadius: 'var(--radius-sm)' }}
                    />
                  ) : (
                    <video
                      src={filePreviewUrl}
                      controls
                      style={{ maxHeight: '200px', maxWidth: '100%', borderRadius: 'var(--radius-sm)' }}
                    />
                  )}
                </div>
              )}
            </div>
          )}

          {/* Action Row */}
          <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
            <div style={{ fontSize: '0.82rem' }}>
              {isProcessing && (
                <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  {progressStage}
                </span>
              )}
              {errorMsg && (
                <span style={{ color: 'var(--veracity-contradicted)', fontFamily: 'var(--font-mono)' }}>
                  {errorMsg}
                </span>
              )}
            </div>

            <button
              onClick={handleVerify}
              disabled={isProcessing}
              className="m-action-btn"
            >
              {isProcessing ? 'Verifying...' : 'Verify Claim'}
            </button>
          </div>

          {/* Quiet Presets Row */}
          <div className="m-presets-bar">
            <span className="m-presets-label">EXAMPLES:</span>
            {BENCHMARK_PRESETS.map((p, idx) => (
              <button
                key={idx}
                onClick={() => handlePresetSelect(p)}
                className="m-preset-pill"
              >
                {p.title}
              </button>
            ))}
          </div>
        </div>

        {/* Verification Results Display */}
        {overallVerdict && (
          <div className="m-result-box">
            {/* Header / Summary */}
            <div className="m-result-header">
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                  <div
                    className="m-verdict-badge"
                    style={{ background: theme.bg, color: theme.color, border: `1px solid ${theme.border}` }}
                  >
                    <span>{theme.label}</span>
                  </div>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                    {(overallConfidence * 100).toFixed(0)}% Confidence • {uncertaintyLevel} Uncertainty {uncertaintyScore !== null ? `(${uncertaintyScore.toFixed(2)})` : ''}
                  </span>
                </div>
                <p style={{ fontSize: '0.92rem', color: 'var(--text-secondary)', maxWidth: '750px', lineHeight: 1.6 }}>
                  {executiveSummary}
                </p>
                {limitations.length > 0 && (
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '8px' }}>
                    Notice: {limitations.join(' • ')}
                  </div>
                )}
              </div>

              {/* View Mode Switcher */}
              <div style={{ display: 'flex', gap: '4px', background: 'var(--bg-subtle)', padding: '3px', borderRadius: 'var(--radius-sm)' }}>
                <button
                  onClick={() => setViewMode('GRAPH')}
                  className={`m-tab-btn ${viewMode === 'GRAPH' ? 'active' : ''}`}
                  style={{ padding: '5px 12px', fontSize: '0.75rem' }}
                >
                  Evidence Graph
                </button>
                <button
                  onClick={() => setViewMode('CITATIONS')}
                  className={`m-tab-btn ${viewMode === 'CITATIONS' ? 'active' : ''}`}
                  style={{ padding: '5px 12px', fontSize: '0.75rem' }}
                >
                  Citations ({currentClaim?.evidence_items?.length || 0})
                </button>
                {(imageForensics || videoForensics) && (
                  <button
                    onClick={() => setViewMode('FORENSICS')}
                    className={`m-tab-btn ${viewMode === 'FORENSICS' ? 'active' : ''}`}
                    style={{ padding: '5px 12px', fontSize: '0.75rem' }}
                  >
                    Forensics
                  </button>
                )}
              </div>
            </div>

            {/* Viewport 1: Topological Evidence Graph */}
            {viewMode === 'GRAPH' && evidenceGraph && (
              <div style={{ background: 'var(--bg-input)', borderRadius: 'var(--radius-md)', padding: '16px', border: '1px solid var(--border-subtle)' }}>
                <EvidenceGraphView
                  graph={evidenceGraph}
                  overallVerdict={overallVerdict}
                />
              </div>
            )}

            {/* Viewport 2: Citations List */}
            {viewMode === 'CITATIONS' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {currentClaim && currentClaim.evidence_items.length > 0 ? (
                  currentClaim.evidence_items.map((ev, i) => (
                    <div
                      key={i}
                      style={{
                        background: 'var(--bg-input)',
                        padding: '16px',
                        borderRadius: 'var(--radius-md)',
                        border: '1px solid var(--border-subtle)',
                        fontSize: '0.82rem'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{ev.source_name || ev.domain}</span>
                        <span
                          style={{
                            fontFamily: 'var(--font-mono)',
                            fontSize: '0.72rem',
                            padding: '2px 8px',
                            borderRadius: 'var(--radius-sm)',
                            color: ev.stance === 'SUPPORTS' ? 'var(--veracity-supported)' : ev.stance === 'REFUTES' ? 'var(--veracity-contradicted)' : 'var(--text-muted)',
                            background: ev.stance === 'SUPPORTS' ? 'var(--veracity-supported-bg)' : ev.stance === 'REFUTES' ? 'var(--veracity-contradicted-bg)' : 'var(--bg-subtle)'
                          }}
                        >
                          {ev.stance}
                        </span>
                      </div>
                      <p style={{ color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '8px' }}>
                        {ev.snippet_text}
                      </p>
                      {ev.source_url && (
                        <a
                          href={ev.source_url}
                          target="_blank"
                          rel="noreferrer"
                          style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textDecoration: 'none' }}
                        >
                          {ev.source_url.slice(0, 70)}... ↗
                        </a>
                      )}
                    </div>
                  ))
                ) : (
                  <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                    No corroborating external citations found.
                  </div>
                )}
              </div>
            )}

            {/* Viewport 3: Media Forensics */}
            {viewMode === 'FORENSICS' && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
                {imageForensics && (
                  <>
                    <div className="m-card">
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Error Level Analysis (ELA)</div>
                      <div style={{ fontSize: '1.1rem', fontWeight: 600, color: imageForensics.is_ela_spliced ? 'var(--veracity-contradicted)' : 'var(--veracity-supported)' }}>
                        {imageForensics.is_ela_spliced ? 'Localized Splicing Detected' : 'Uniform Compression'}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>Max Error: {imageForensics.ela_max_error}</div>
                    </div>
                    <div className="m-card">
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Synthetic Indicator</div>
                      <div style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                        {(imageForensics.synthetic_probability * 100).toFixed(0)}%
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>Confidence: {imageForensics.synthetic_confidence}</div>
                    </div>
                    {ocrText && (
                      <div className="m-card" style={{ gridColumn: '1 / -1' }}>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>OCR Extracted Text</div>
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>"{ocrText}"</div>
                      </div>
                    )}
                  </>
                )}

                {videoForensics && (
                  <>
                    <div className="m-card">
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Duration & Scenes</div>
                      <div style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {videoForensics.duration_seconds.toFixed(1)}s • {videoForensics.extracted_scenes} scenes
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                        Audio: {videoForensics.has_audio_track ? 'Detected' : 'Silent'}
                      </div>
                    </div>
                    {transcriptText && (
                      <div className="m-card" style={{ gridColumn: '1 / -1' }}>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Whisper Speech Transcript</div>
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>"{transcriptText}"</div>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        )}
      </main>

      {/* Streamlined Secondary Sections with Generous Whitespace */}
      <ArchitectureSection />
      <ResearchBenchmarkTable />
      <MethodologySection />
      <Footer />
    </div>
  );
}

export default App;
