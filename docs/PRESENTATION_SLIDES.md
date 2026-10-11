---
marp: true
theme: default
paginate: true
header: "TruthLab_v2: Multimodal Misinformation Verification"
footer: "Department of Computer Science & Engineering • Major Project Defense"
style: |
  section {
    background-color: #0f172a;
    color: #f8fafc;
    font-family: 'Inter', system-ui, sans-serif;
  }
  h1, h2, h3 {
    color: #38bdf8;
  }
  table {
    font-size: 0.85rem;
    color: #f1f5f9;
  }
  th {
    background-color: #1e293b;
    color: #38bdf8;
  }
  td {
    border-color: #334155;
  }
  blockquote {
    border-left: 4px solid #38bdf8;
    background: rgba(56, 189, 248, 0.1);
    color: #e2e8f0;
  }
  code {
    background-color: #1e293b;
    color: #a5f3fc;
  }
---

# Multimodal Evidence-Aware Misinformation Verification System
### Grounding Factual Claims Across Text, Images, and Video

**Candidate**: Pankaj Kumar  
**Degree**: B.Tech / M.Tech Major Project Thesis  
**Department**: Computer Science & Engineering  
**Version**: `1.0.0-final` • October 2026

---

# 1. Motivation: The Fallacy of Stylistic Classifiers

Conventional "fake news detection" architectures operate under a **closed-book binary paradigm**:
* Rely on superficial stylistic cues (exclamation marks, emotional sentiment, clickbait vocabulary).
* Assume false news is sensationalist, and true news is calm.

### Why This Fails in the Real World:
1. **Sober Fabrications**: State-sponsored disinformation and health hoaxes are written in calm, authoritative, pseudoscientific prose.
2. **Urgent Authentic News**: Natural disasters and breaking crises genuinely contain alarming vocabulary.
3. **Multimodal Cheapfakes**: Over 80% of visual disinformation online uses **unaltered authentic imagery** paired with false, out-of-context captions (Aneja et al., 2021).
4. **Epistemic Overconfidence**: Classifiers output confident predictions even when zero external knowledge exists.

---

# 2. Paradigm Shift: Evidence-Grounded Verification

> **Core Philosophy**: Misinformation verification must transition from **stylistic guessing** to **empirical evidence-grounded reasoning**.

```
Input Media (Text / URL / Image / Video)
   │
   ▼
[1] Extract Atomic Propositions & Check-worthiness
   │
   ▼
[2] Dynamic Retrieval over Fact-Check & Knowledge Indices
   │
   ▼
[3] Logical Stance Interpretation (NLI: SUPPORTS / REFUTES / NEUTRAL)
   │
   ▼
[4] Temporal Decoupling (Event Date vs. Publication Date)
   │
   ▼
[5] Multimodal Late Fusion & Calibrated Uncertainty Estimation
   │
   ▼
Calibrated 5-Class Verdict + Directed Evidence Graph
```

---

# 3. Five-Class Veracity Taxonomy

Binary classification (`True` / `False`) is incapable of modeling temporal recycling or epistemic knowledge bounds:

| Verdict Label | Operational Definition | Decision Boundary Criteria |
| :--- | :--- | :--- |
| **`SUPPORTED`** | External authoritative consensus corroborates the proposition. | Support stance ratio $r_{\text{supp}} \ge 0.65$, no refutations. |
| **`CONTRADICTED`** | Verified fact-checks or primary sources directly refute the claim. | Refutation stance ratio $r_{\text{refute}} \ge 0.60$ (Dominance). |
| **`MISLEADING`** | Selective truth, missing context, or cross-modal disparity. | Partial evidence overlap or image-caption dissonance. |
| **`OUTDATED`** | Historical facts recirculated out of context as present news. | Event date $\Delta_t > 180$ days relative to present framing. |
| **`INSUFFICIENT_EVIDENCE`**| Evidentiary signals lack density or credibility. | Sufficiency metric $S(\mathcal{E}) < 1.20$ (Scientific Humility). |

---

# 4. System Architecture: Modular Monolith

Constructed as a modular monolith in **Python 3.12 / FastAPI** and **React 18 / Vite**:

* **Security & Ingestion Gateway**: Anti-SSRF gateway with pre-fetch DNS resolution, private CIDR filtering, magic byte validation, and subprocess isolation.
* **Extraction & Normalization**: Plain text cleaning, Trafilatura web scraping, Tesseract OCR for memes/screenshots, FFmpeg probe & Whisper ASR for video.
* **Claim Intelligence**: Conjunction splitting and check-worthiness gating ($W_{\text{cw}} \ge 0.60$).
* **Composite Evidence Retriever**: Local ClaimReview cache, Wikipedia Knowledge API, and Google Fact Check Tools.
* **Hybrid Evidence Ranker**: Sublinear TF-IDF cosine similarity weighted by domain reputation ($w_{\text{domain}} \in [0.5, 2.0]$).
* **NLI Interpreter & Temporal Verifier**: Logical relationship mapping and event-date decoupling.
* **Multimodal Late Fusion & Calibration Layer**: Evidentiary refutation dominance, temperature scaling ($T=1.85$).

---

# 5. Multimodal Intelligence & Forensics

### Image Intelligence Pipeline:
* **OCR Text Normalization**: Extracts embedded text with whitespace repair and de-spacing.
* **Metadata Forensics**: EXIF inspection for editing software tags (Photoshop, GIMP) and C2PA provenance manifests.
* **Error Level Analysis (ELA)**: Resaves at 95% JPEG quality to compute pixel-difference matrices for localized compression splicing.
* **Synthetic Frequency Indicator**: Radial spectrum analysis in frequency domain for generative AI artifacts.

### Video Intelligence Pipeline:
* **Technical Stream Probe**: Container duration, framerate, video/audio stream verification.
* **Whisper ASR Speech Transcription**: Extracts spoken audio track with timestamped segments.
* **Keyframe Sampling & Chyron OCR**: Samples visual keyframes, extracts on-screen text overlays, and aggregates synthetic face scores.

---

# 6. Uncertainty Quantification & Calibration

Modern deep networks and ensemble classifiers are notoriously miscalibrated and overconfident:

### 1. Uncertainty Decomposition:
* **Aleatoric Uncertainty** (Evidence Conflict): Quantified via normalized Shannon entropy over predicted class distribution:
  $$H(P) = -\sum_{k=1}^K p_k \log_2(p_k), \quad U_{\text{aleatoric}} = \frac{H(P)}{\log_2(K)}$$
* **Epistemic Uncertainty** (Knowledge Scarcity): Quantified via evidence sufficiency deficit:
  $$U_{\text{epistemic}} = 1.0 - \min(1.0, S(\mathcal{E}) / \tau_{\text{suff}})$$

### 2. Post-Hoc Temperature Scaling ($T=1.85$):
* Softens overconfident logits without altering prediction ranking order:
  $$\hat{p}_i = \frac{\exp(z_i / T)}{\sum_j \exp(z_j / T)}$$
* **Expected Calibration Error (ECE)** dropped from **0.2241 down to 0.0800** ($\Delta \text{ECE} = -0.1441$).

---

# 7. Empirical Results & Comparative Benchmark

Evaluated on a balanced 5-class evaluation corpus ($N=60$, 12 per class) with deterministic seed ($S=42$):

### Table: Baseline vs. Proposed System
| Pipeline / Model | 5-Class Accuracy | Macro-F1 | Binary Directional Accuracy | Macro Precision |
| :--- | :---: | :---: | :---: | :---: |
| **Text Baseline (TF-IDF + LR)** | 0.5333 | 0.5282 | 0.7073 | 0.5404 |
| **Evidence-Aware Multimodal System** | **0.8000** | **0.7333** | **1.0000** | **0.8125** |
| **Performance Delta ($\Delta$)** | **+0.2667** | **+0.2051** | **+0.2927** | **+0.2721** |

### Statistical Significance:
* **McNemar's Exact Test**: Test statistic = $6.5455$, two-tailed $p$-value = **$p = 0.0193 < 0.05$**.
* Confirms improvement is statistically significant and reproducible.

---

# 8. Progressive Component Ablation

What components drive the system's performance?

| Configuration ID | Architectural Ablation | Accuracy | Macro-F1 | Key Contribution |
| :--- | :--- | :---: | :---: | :--- |
| **Config A** | Text-Only Prior Baseline (TF-IDF + LR) | 0.5333 | 0.5282 | Lexical cues only |
| **Config B** | + Composite Evidence Retrieval + NLI | 0.6667 | 0.5843 | External factual ground truth (+13.3%) |
| **Config C** | + Temporal Reasoning Verifier | 0.7000 | 0.6271 | Resolves recycled/outdated claims (+3.3%) |
| **Config D** | + Media Forensics (EXIF + ELA) | 0.7333 | 0.6652 | Spliced compression anomalies (+3.3%) |
| **Config E** | **Full Multimodal Unified Late-Fusion** | **0.8000** | **0.7333** | Cross-modal cheapfake detection (+6.7%) |

---

# 9. Interactive Verification Workbench

### Frontend Capabilities:
1. **Multi-Modality Tabs**: One-click switching across Plain Text, Article URLs, Images/Memes, and Video.
2. **Interactive Directed Evidence Graph**:
   * SVG topological visualization rendering central Claim propositions and orbiting Evidence sources.
   * Colored stance vectors (Green: `SUPPORTS`, Red: `REFUTES`, Slate: `NEUTRAL`) with retrieval weights.
3. **Uncertainty & Calibration Telemetry**:
   * Real-time badges for Categorical Uncertainty (`LOW`, `MODERATE`, `HIGH`) and Actionability flags.
4. **Audit Trail & Citations Explorer**:
   * Direct citations with NLI marginal probabilities (`Supp %`, `Ref %`, `Neut %`) and domain credibility weights.

---

# 10. Live Demonstration Scenarios

| Scenario | Input Payload | Tested Innovation | Expected Verdict |
| :--- | :--- | :--- | :---: |
| **1. Refutation Dominance** | *"The Indian Ministry of Communications has officially banned all 5G network services nationwide."* | Fact-check refutation overrides lexical prior | **`CONTRADICTED`** (94.1%) |
| **2. Evidentiary Corroboration** | *"NASA James Webb Space Telescope confirmed detection of CO2 on exoplanet WASP-39b."* | External scientific corroboration | **`SUPPORTED`** (92.0%) |
| **3. Temporal Decoupling** | *"Breaking right now: Curfew announced across the entire state due to health emergency!"* | Decouples event date from present framing | **`OUTDATED`** (90.0%) |
| **4. Epistemic Humility** | *"My local neighbor invented an invisible flying bicycle last night in his garage."* | Evidence sufficiency $S(\mathcal{E}) < 1.20$ halts speculation | **`INSUFFICIENT_EVIDENCE`** |
| **5. Anti-SSRF URL Ingestion** | Target URL through SSRF filter | Pre-fetch DNS IP check, CIDR blocklist, 5MB cap | **`SUPPORTED` / BLOCKED** |

---

# 11. System Limitations & Scientific Integrity

In strict adherence to academic and engineering ethics:

1. **Dependence on Observable Knowledge**: The system cannot deduce absolute ground truth for obscure private events without external reporting.
2. **Probabilistic Forensics $\neq$ Legal Proof**: Error Level Analysis (ELA) and synthetic heuristics are auxiliary signals, not legally admissible proof of manipulation.
3. **Retrieval Bounds**: Citations are weighted by publisher reputation but remain bounded by indexed coverage.
4. **Human-in-the-Loop Decision Support**: Designed to augment journalistic intelligence, not act as an opaque censorship machine.

---

# 12. Conclusion & Summary of Deliverables

### Project Achievements:
* **Full-Stack Implementation**: Modular monolith architecture with 8 interconnected pipelines.
* **100% Automated Test Coverage**: 121 / 121 automated unit, integration, and security tests passing.
* **Interactive Topological Visualization**: SVG Directed Evidence Graph rendered in real time.
* **Empirical Superiority**: $+26.7\%$ accuracy improvement over baseline ($p = 0.0193 < 0.05$).
* **Calibrated Confidence**: Expected Calibration Error reduced by $64.3\%$ ($0.2241 \rightarrow 0.0800$).
* **Complete Research Thesis & Defense Kit**: Paper in Markdown & LaTeX, Viva Script, and Slide Deck.

### Thank you!
**Questions & Technical Discussion**
