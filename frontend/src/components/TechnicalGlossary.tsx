import React from 'react';

export const TechnicalGlossary: React.FC = () => {
  const glossaryTerms = [
    {
      term: "Anti-SSRF Socket Shield",
      formula: "IP ∉ {RFC 1918, RFC 3927, 127.0.0.0/8, 169.254.169.254}",
      definition: "Pre-fetch DNS resolution hook that resolves destination hostnames prior to HTTP request dispatch. Rejects private, loopback, link-local, and cloud metadata IPs to prevent internal network scanning."
    },
    {
      term: "Binary Magic Byte Validation",
      formula: "Header[0:4] == \\xFF\\xD8\\xFF | \\x89PNG | ftyp | \\x1A\\x45\\xDF\\xA3",
      definition: "Inspection of raw leading file byte signatures before invoking media decoders. Enforces file identity at the byte level, neutralizing polyglot payload attacks and MIME-type header spoofing."
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
    <section id="glossary" className="py-16 px-6 max-w-7xl mx-auto border-t border-white/5">
      <div className="mb-12">
        <div className="flex items-center gap-2 font-mono text-xs text-sky-400 font-semibold mb-2">
          <span>// RIGOROUS TECHNICAL GLOSSARY</span>
        </div>
        <h2 className="text-3xl font-extrabold text-white tracking-tight sm:text-4xl">
          Core Technical Terms & Mechanics
        </h2>
        <p className="mt-3 text-slate-400 text-sm max-w-3xl leading-relaxed">
          Zero marketing fluff. Below are the exact architectural definitions, mathematical formulations, and
          operational roles of the technologies powering TruthLab v2.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {glossaryTerms.map((item, idx) => (
          <div
            key={idx}
            className="p-5 rounded-xl bg-slate-900/60 border border-white/10 hover:border-indigo-500/30 transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-start justify-between gap-3 mb-2">
                <h3 className="font-bold text-white text-base">{item.term}</h3>
                <span className="font-mono text-[11px] text-slate-500">[{idx + 1}]</span>
              </div>
              <div className="p-2.5 rounded bg-black/40 border border-white/5 font-mono text-[11px] text-sky-300 mb-3 overflow-x-auto">
                {item.formula}
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-sans">{item.definition}</p>
            </div>
            <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-[11px] font-mono text-slate-500">
              <span>Mechanic Grounded</span>
              <span className="text-emerald-400">Strict Spec ✓</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};
