import React from 'react';

export const ForensicsDeepDive: React.FC = () => {
  return (
    <section id="forensics" className="py-16 px-6 max-w-7xl mx-auto border-t border-white/5">
      <div className="mb-12">
        <div className="flex items-center gap-2 font-mono text-xs text-sky-400 font-semibold mb-2">
          <span>// FORENSIC SIGNAL ANALYSIS</span>
        </div>
        <h2 className="text-3xl font-extrabold text-white tracking-tight sm:text-4xl">
          Multi-Layer Forensic Modalities
        </h2>
        <p className="mt-3 text-slate-400 text-sm max-w-3xl leading-relaxed">
          Unlike black-box models that issue opaque predictions, TruthLab inspects mathematical compression residuals,
          discrete frequency distributions, and audio-visual temporal alignment to expose manipulation.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Module A: Error Level Analysis */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-white/10 hover:border-sky-500/30 transition-all">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-sky-400"></span>
              Error Level Analysis (ELA)
            </h3>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20">
              Compression Residuals
            </span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed mb-4">
            When an image is saved in JPEG format, its discrete cosine transform (DCT) coefficients are quantized
            at an approximately uniform error rate. If an object is digitally spliced in from an external source or edited,
            its localized error rate diverges from the rest of the image.
          </p>
          
          <div className="p-4 rounded-lg bg-black/40 border border-white/5 font-mono text-xs mb-4 text-slate-300 space-y-2">
            <div className="text-slate-400">// Differential Matrix Calculation (Q = 90)</div>
            <div className="text-sky-300">ΔI(x, y) = |I_orig(x, y) - I_resaved(x, y)|</div>
            <div className="text-slate-400">// Regional 16x16 DCT Block Variance</div>
            <div className="text-indigo-300">Variance_block &gt; (Mean_diff * 2.5 + 0.05) → Flagged Splicing</div>
          </div>

          <div className="text-[11px] text-slate-400 leading-relaxed">
            <strong className="text-slate-200">Guaranteed Academic Caveat:</strong> ELA identifies compression irregularities;
            it is combined with semantic evidence rather than treated as unilateral proof, protecting against false positives from social media re-encoding.
          </div>
        </div>

        {/* Module B: Synthetic Media Heuristics */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-white/10 hover:border-indigo-500/30 transition-all">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-400"></span>
              Synthetic Diffusion Frequency (σ²_∇²)
            </h3>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              Frequency Heuristics
            </span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed mb-4">
            Generative diffusion models (Midjourney, DALL-E, Stable Diffusion) generate images with characteristic
            high-saturation dispersion profiles and unnatural Laplacian gradient smoothness along structural boundaries.
          </p>

          <div className="p-4 rounded-lg bg-black/40 border border-white/5 font-mono text-xs mb-4 text-slate-300 space-y-2">
            <div className="text-slate-400">// Discrete Laplacian Spatial Second-Derivative</div>
            <div className="text-indigo-300">σ²_∇² = Var(∂²I/∂x²) + Var(∂²I/∂y²)</div>
            <div className="text-slate-400">// Prior-Bounded Continuous Likelihood</div>
            <div className="text-emerald-300">P(synthetic) ∈ [0.05, 0.95] (Strictly Bounded)</div>
          </div>

          <div className="text-[11px] text-slate-400 leading-relaxed">
            <strong className="text-slate-200">Anti-Overconfidence Bound:</strong> Synthetic likelihood is bounded to [0.05, 0.95]
            to explicitly reject false absolute certainties, accommodating camera noise profiles and compression artifacts.
          </div>
        </div>

        {/* Module C: Video Audio-Visual Dual Channel */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-white/10 hover:border-purple-500/30 transition-all">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-400"></span>
              Whisper ASR & Scene Chyron Alignment
            </h3>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
              Cross-Modal Temporal
            </span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed mb-4">
            Video misinformation frequently pairs genuine video clips with deceptive audio, or overlays false "BREAKING NEWS"
            tickers over unrelated footage. TruthLab demuxes both streams in parallel:
          </p>

          <div className="grid grid-cols-2 gap-3 mb-4 text-xs font-mono">
            <div className="p-3 rounded bg-black/30 border border-white/5">
              <span className="text-purple-300 block font-semibold mb-1">Audio Track:</span>
              <span className="text-slate-400 text-[11px]">16kHz Mono WAV → Whisper ASR speech segments</span>
            </div>
            <div className="p-3 rounded bg-black/30 border border-white/5">
              <span className="text-sky-300 block font-semibold mb-1">Visual Track:</span>
              <span className="text-slate-400 text-[11px]">Keyframe scene OCR → Chyron & banner texts</span>
            </div>
          </div>

          <p className="text-[11px] text-slate-400">
            Both text corpora are unified into atomic propositions and queried simultaneously, exposing out-of-context audio overdubs.
          </p>
        </div>

        {/* Module D: Epistemic Refusal vs Hallucination */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-white/10 hover:border-emerald-500/30 transition-all">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
              Epistemic Refusal & Temporal Decay
            </h3>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Hallucination Guard
            </span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed mb-4">
            Standard LLMs hallucinate assertions when presented with uninformative imagery. TruthLab incorporates
            academic refusal thresholds and time-decay rules:
          </p>

          <div className="space-y-2 mb-4 text-xs font-mono">
            <div className="p-2.5 rounded bg-black/30 border border-white/5 text-[11px] flex justify-between items-center">
              <span className="text-slate-300">Non-textual / Artistic Media:</span>
              <span className="text-amber-400 font-bold">INSUFFICIENT_EVIDENCE</span>
            </div>
            <div className="p-2.5 rounded bg-black/30 border border-white/5 text-[11px] flex justify-between items-center">
              <span className="text-slate-300">Evidence Sufficiency &lt; 1.20:</span>
              <span className="text-sky-400 font-bold">Withhold Veracity</span>
            </div>
            <div className="p-2.5 rounded bg-black/30 border border-white/5 text-[11px] flex justify-between items-center">
              <span className="text-slate-300">Context Delta &gt; 180 Days:</span>
              <span className="text-purple-400 font-bold">Flag as OUTDATED</span>
            </div>
          </div>

          <p className="text-[11px] text-slate-400">
            Guarantees that the system refuses to speculate on ungrounded claims or recycled historical notices.
          </p>
        </div>
      </div>
    </section>
  );
};
