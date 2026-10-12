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
        "Payload quotas: <= 15MB images, <= 60MB videos, max duration <= 90s strictly enforced."
      ]
    },
    {
      num: "02",
      title: "Feature & Signal Extraction",
      tag: "Multimodal Decomposition",
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
      tag: "Dual-Channel Grounding",
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
    <section id="pipeline" className="py-16 px-6 max-w-7xl mx-auto border-t border-white/5">
      <div className="mb-12">
        <div className="flex items-center gap-2 font-mono text-xs text-sky-400 font-semibold mb-2">
          <span>// PIPELINE SPECIFICATION</span>
        </div>
        <h2 className="text-3xl font-extrabold text-white tracking-tight sm:text-4xl">
          Multimodal Verification Architecture
        </h2>
        <p className="mt-3 text-slate-400 text-sm max-w-3xl leading-relaxed">
          TruthLab operates as an asynchronous pipeline with mathematical logit calibration,
          cross-modal consistency checks, and multi-tier evidentiary retrieval—rejecting ungrounded AI guesses.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stages.map((stage) => (
          <div
            key={stage.num}
            className="p-6 rounded-xl bg-slate-900/60 border border-white/10 flex flex-col justify-between hover:border-indigo-500/40 transition-all relative overflow-hidden group"
          >
            <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/5 rounded-bl-full pointer-events-none group-hover:bg-indigo-500/10 transition-colors" />
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="font-mono text-2xl font-black text-indigo-400/80">{stage.num}</span>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-white/5 text-slate-300 border border-white/5">
                  {stage.tag}
                </span>
              </div>
              <h3 className="text-lg font-bold text-white mb-2">{stage.title}</h3>
              <p className="text-xs text-slate-400 mb-4 leading-relaxed">{stage.desc}</p>
              
              <ul className="space-y-2 border-t border-white/5 pt-4">
                {stage.mechanics.map((item, idx) => (
                  <li key={idx} className="text-[11px] text-slate-300 flex items-start gap-2 leading-relaxed">
                    <span className="text-sky-400 font-mono mt-0.5">›</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-6 pt-3 border-t border-white/5 flex items-center justify-between text-[11px] font-mono text-slate-500">
              <span>Verified Module</span>
              <span className="text-emerald-400 font-semibold">Ready ✓</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};
