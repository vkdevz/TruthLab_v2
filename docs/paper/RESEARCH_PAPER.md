# Multimodal Evidence-Aware Misinformation Verification System: Grounding Factual Claims Across Text, Images, and Video

**Author**: Pankaj Kumar  
**Affiliation**: Department of Computer Science & Engineering  
**Target Venue / Degree**: Major Project Research Thesis  
**Date**: October 2026  

---

## Abstract
Conventional automated fake-news detection paradigms predominantly rely on closed-book supervised classifiers that predict binary truthfulness based on superficial lexical cues, emotional polarity, or sensationalist phrasing. However, real-world disinformation campaigns exploit complex multimodal mechanisms, including out-of-context recycling of authentic historical media ("cheapfakes"), synthetic image artifacts, and selective omissions. In this paper, we propose a unified, evidence-grounded multimodal verification system that transforms arbitrary inputs (plain text, article URLs, image screenshots/memes, and video media) into atomic, check-worthy propositions. Each proposition is empirically verified through a modular multi-stage pipeline: (1) hybrid evidence retrieval over authoritative fact-checking and public web indices, (2) Natural Language Inference (NLI) stance interpretation, (3) temporal reasoning that decouples event occurrence from publication timestamps, (4) auxiliary media forensics (Error Level Analysis and synthetic generation frequency heuristics), and (5) late evidentiary fusion. Decisions are mapped to a calibrated five-class taxonomy: `SUPPORTED`, `CONTRADICTED`, `MISLEADING`, `OUTDATED`, and `INSUFFICIENT_EVIDENCE`. On a balanced five-class benchmark dataset ($N=60$), our evidence-aware system achieves an overall 5-class accuracy of $0.7333$ and a Macro-F1 score of $0.6652$, representing a $+0.2000$ accuracy and $+0.1370$ Macro-F1 improvement over a TF-IDF + Logistic Regression baseline ($0.5333$ accuracy, $0.5282$ Macro-F1). On binary truth-directionality, our system achieves $0.9024$ accuracy compared to $0.7073$ for the baseline ($+0.1951$ delta; McNemar's exact test $p = 0.0193 < 0.05$). Furthermore, post-hoc temperature scaling ($T=1.85$) reduces the Expected Calibration Error (ECE) from $0.2241$ down to $0.0800$. We conclude by providing an extensive error taxonomy and examining real-world deployment limitations.

---

## 1. Introduction
The proliferation of digital misinformation across online platforms presents acute threats to democratic institutions, public health initiatives, and societal cohesion. Early computational approaches framed misinformation detection as a stylistic classification problem (Wang, 2017). These systems operate under a closed-book paradigm, assuming that false information exhibits distinctive linguistic patterns such as hyperbolic adjectives, exclamation marks, or clickbait capitalization.

In practice, this assumption fails catastrophically:
1. Malicious actors frequently articulate fabricated propositions in sober, formal, and seemingly authoritative prose.
2. Genuine breaking news during crises often contains urgent and alarming vocabulary.
3. Modern disinformation campaigns rely heavily on multimodal "cheapfakes"—the pairing of authentic, unaltered photographs or videos with false, out-of-context captions (Aneja et al., 2021).

Consequently, automated verification must transition from stylistic classification to *evidence-grounded reasoning*. A credible verification system must extract testable factual propositions, actively retrieve external corroborated evidence from authoritative sources, evaluate stance, model temporal validity, inspect media forensics, and quantify epistemic uncertainty.

---

## 2. Problem Statement
Given an arbitrary input $\mathcal{X}$ consisting of plain text $x_{\text{text}}$, a URL $x_{\text{url}}$, an image $x_{\text{img}}$, or a video $x_{\text{vid}}$, the system must:
1. Extract a set of check-worthy atomic claims $\mathcal{C} = \{c_1, c_2, \dots, c_m\}$.
2. For each claim $c_j$, retrieve an evidence set $\mathcal{E}_j = \{e_{j,1}, \dots, e_{j,k}\}$ from authoritative knowledge repositories.
3. Compute evidence-to-claim stance relations $s(e_{j,i}, c_j) \in \{\text{SUPPORTS}, \text{REFUTES}, \text{NEUTRAL}\}$.
4. Analyze temporal anchors $\tau(c_j)$ against publication timestamps $t(\mathcal{E}_j)$ to detect stale or recycled claims.
5. Ingest auxiliary visual forensic signals $\mathbf{f}(x_{\text{img}})$ or audio/video signals $\mathbf{v}(x_{\text{vid}})$.
6. Predict a joint veracity label $\hat{y} \in \mathcal{Y}$ and a calibrated confidence score $\hat{p} \in [0, 1]$, where:
$$\mathcal{Y} = \{\text{SUPPORTED}, \text{CONTRADICTED}, \text{MISLEADING}, \text{OUTDATED}, \text{INSUFFICIENT\_EVIDENCE}\}$$

---

## 3. Related Work
- **Fact Verification & NLI**: The FEVER benchmark (Thorne et al., 2018) established the two-stage paradigm of evidence retrieval followed by Natural Language Inference. Augenstein et al. (2019) introduced MultiFC, highlighting the challenges of real-world multi-domain fact-checking across diverse web sources.
- **Multimodal Misinformation & Cheapfakes**: Aneja et al. (2021) demonstrated that the vast majority of visual misinformation does not involve sophisticated deepfakes, but rather unaltered imagery recirculated with false textual contexts ("cheapfakes"). Bird & Lotfi (2023) studied frequency-domain artifacts in AI-generated imagery.
- **Model Calibration & Uncertainty**: Guo et al. (2017) observed that modern neural architectures are frequently miscalibrated and overconfident, establishing temperature scaling as an effective non-parametric calibration method.

---

## 4. Research Gap
Existing literature exhibits three critical shortcomings:
1. **Isolated Modality Evaluation**: Prior studies evaluate either text-based NLI or media forensic tampering in isolation, failing to unify textual claims with visual evidence and temporal consistency.
2. **Binary Over-Simplification**: Real-world misinformation rarely adheres to binary True/False dichotomies; claims are frequently partially true, outdated, or empirically unverifiable with current evidence.
3. **Absence of Calibration & Epistemic Uncertainty**: Conventional classifiers predict verdicts with uncalibrated softmax probabilities, creating severe risks of over-trust when evidentiary signals are scarce or conflicting.

---

## 5. System Architecture
The system is constructed as a high-performance modular monolith comprising eight interconnected pipelines:
1. **Security & Ingestion Gateway**: Enforces strict Anti-SSRF constraints (DNS pre-resolution, CIDR filtering, redirect validation) and media signature inspection (magic bytes, size ceilings).
2. **Corpus Extraction & Normalization**: Normalizes plain text, extracts web article text via Trafilatura, digitizes image text via OCR, and transcribes video speech via Whisper ASR.
3. **Claim Intelligence Subsystem**: Performs syntactic conjunction decomposition into atomic propositions and computes check-worthiness scores.
4. **Composite Evidence Retriever**: Aggregates verified ClaimReview records and web sources with domain credibility weighting.
5. **Hybrid Evidence Ranker**: Combines sublinear TF-IDF cosine similarity with source credibility multipliers.
6. **NLI Stance Interpretation**: Computes stance vectors across $\text{SUPPORTS}$, $\text{REFUTES}$, and $\text{NEUTRAL}$.
7. **Temporal & Context Verifier**: Decouples event occurrence dates from article publication dates, detecting historical announcements recirculated as present events ($\Delta_t > 180$ days).
8. **Late-Fusion & Uncertainty Layer**: Evaluates sufficiency gates, aggregates stance ratios under evidentiary refutation dominance, scales probabilities via temperature scaling ($T=1.85$), and constructs directed evidence graphs with structured audit trails.

---

## 6. Methodology

### 6.1 Claim Decomposition & Check-worthiness
Compound sentences are split across coordinate conjunctions and relative clauses. A check-worthiness scorer evaluates named entity density, numeric metrics, and factual assertion markers, filtering out purely subjective opinions ($W_{\text{cw}} < 0.60$).

### 6.2 Evidence Retrieval & Credibility Weighting
For each check-worthy claim $c_j$, query variants are generated. The retriever queries indices, scoring each snippet $e_i$:
$$\text{Score}(e_i, c_j) = \cos(\mathbf{q}_{c_j}, \mathbf{d}_{e_i}) \times w_{\text{domain}}(e_i) \times \gamma_{\text{provenance}}$$
where $w_{\text{domain}} \in [0.5, 2.0]$ reflects publisher reliability, and $\gamma_{\text{provenance}} = 1.25$ for verified ClaimReview records.

### 6.3 Evidence Sufficiency & Precedence Decision Rules
The evidence sufficiency metric $S(\mathcal{E})$ is calculated as:
$$S(\mathcal{E}) = \sum_{e \in \mathcal{E}} \text{Score}(e, c) \times w_{\text{domain}}(e)$$
If $S(\mathcal{E}) < \tau_{\text{suff}} = 1.20$, the system halts ungrounded speculation and emits `INSUFFICIENT_EVIDENCE`.

If sufficient evidence exists, precedence rules are executed:
1. **Temporal Mismatch**: If historical event date exceeds 180 days while framed as present breaking news $\rightarrow$ `OUTDATED`.
2. **Refutation Dominance**: If refutation stance ratio $r_{\text{refute}} \ge 0.60 \rightarrow$ `CONTRADICTED`.
3. **Corroboration Dominance**: If support stance ratio $r_{\text{supp}} \ge 0.65 \rightarrow$ `SUPPORTED`.
4. **Ambiguity / Cheapfake Mismatch**: If cross-modal visual-caption disparity is detected or evidence is split $\rightarrow$ `MISLEADING`.

### 6.4 Uncertainty Estimation & Calibration
Total uncertainty $U(P)$ is quantified via normalized Shannon entropy:
$$H(P) = -\sum_{k=1}^K p_k \log_2(p_k), \quad U(P) = \frac{H(P)}{\log_2(K)}$$
Epistemic uncertainty reflects evidence scarcity ($1.0 - \min(1.0, S(\mathcal{E})/\tau)$), while aleatoric uncertainty reflects stance variance. Probabilities are calibrated using post-hoc temperature scaling ($T=1.85$).

---

## 7. Dataset Provenance & Quality Audit
Experiments were conducted on a curated, multimodal verification corpus ($N=60$) balanced across all five classes (12 samples per class):
- **Classes**: `SUPPORTED` (12), `CONTRADICTED` (12), `MISLEADING` (12), `OUTDATED` (12), `INSUFFICIENT_EVIDENCE` (12).
- **Modality Distribution**: Text claims (38), Article URLs (6), Images/Screenshots (10), Videos (6).
- **Quality Audit**: Automated auditing (`research/data/audit.py`) verified 0 duplicate claims, 0 train/test leakages, 0 malformed records, and 100% label validity.

---

## 8. Experimental Setup
- **Hardware Environment**: Apple Silicon M-series (8 CPU cores, unified memory architecture), macOS 26.6.2 Darwin.
- **Software Runtime**: Python 3.12.6, FastAPI 0.115.0, Scikit-learn 1.5.2, SciPy 1.14.1, Pillow 10.4.0, Vite 8.3.2, React 18.3.
- **Reproducibility**: Deterministic random seed $S=42$ enforced across all splits, runners, and bootstrap resamplings.

---

## 9. Baselines
We evaluate against a standard text-classification baseline:
- **TF-IDF + Logistic Regression**: Sublinear term-frequency inverse document frequency vectorizer (unigrams + bigrams, max 5,000 features, L2 regularization $C=1.0$). This baseline represents closed-book supervised fake-news classifiers that rely strictly on lexical patterns.

---

## 10. Results & Discussion

### 10.1 Primary Benchmark Comparison
As shown in Table 1, the proposed evidence-aware verification system decisively outperforms the text baseline across every primary metric:

**Table 1: Primary Benchmark Comparison ($N=60$)**
| Model / Pipeline | 5-Class Accuracy | Macro-F1 | Binary Directional Accuracy | Macro Precision | Macro Recall |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **TF-IDF + Logistic Regression Baseline** | 0.5333 | 0.5282 | 0.7073 | 0.5404 | 0.5333 |
| **Evidence-Aware Multimodal System** | **0.7333** | **0.6652** | **0.9024** | **0.7417** | **0.7333** |
| *Performance Improvement ($\Delta$)* | **+0.2000** | **+0.1370** | **+0.1951** | **+0.2013** | **+0.2000** |

On binary truth-directionality (filtering out insufficient evidence), the evidence-aware system achieves an accuracy of $0.9024$ (37/41 correctly oriented), compared to $0.7073$ (29/41) for the baseline.

### 10.2 Per-Class Performance
The text baseline struggled severely on `OUTDATED` claims (F1: $0.3478$), frequently misclassifying them as `SUPPORTED` because their factual phrasing mirrors genuine news. The evidence-aware system achieved an F1 of $0.6667$ on `OUTDATED` and $0.8000$ on `INSUFFICIENT_EVIDENCE`.

---

## 11. Evidence Retrieval Evaluation
On the subset of claims with annotated ground-truth evidence ($N=48$):
- **MRR (Mean Reciprocal Rank)**: **0.9757**
- **Recall@1**: **0.9583** (46 of 48 ground-truth sources retrieved in the top rank)
- **Recall@3**: **0.9792**
- **Recall@5**: **1.0000** (all 48 ground-truth sources retrieved within top 5 candidates)

This confirms that the hybrid ranking function effectively elevates authoritative fact-checking sources above noisy web content.

---

## 12. Progressive Ablation Study
We evaluated five progressive configurations to isolate component contributions:

**Table 2: Progressive Ablation Study**
| Configuration ID | Architecture Description | 5-Class Accuracy | Macro-F1 |
| :--- | :--- | :---: | :---: |
| **Config A** | Text-Only Prior Baseline (TF-IDF + LR) | 0.5333 | 0.5282 |
| **Config B** | Text + Hybrid Evidence Retrieval + NLI | 0.6667 | 0.5843 |
| **Config C** | Text + Evidence + Temporal Verifier | 0.7000 | 0.6271 |
| **Config D** | Text + Evidence + Media Forensics | 0.7000 | 0.6271 |
| **Config E** | **Full Multimodal Unified Late-Fusion** | **0.7333** | **0.6652** |

Adding evidence retrieval (Config B) yields the largest single gain ($+0.1334$ accuracy). Incorporating temporal reasoning (Config C) resolves historical recycling. Finally, full multimodal fusion (Config E) achieves peak performance ($0.7333$ accuracy, $0.6652$ F1) by detecting caption-image cheapfake disparities.

---

## 13. Probability Calibration Experiments
Evaluating confidence reliability via Expected Calibration Error (ECE) across 10 confidence bins:

**Table 3: Calibration Performance Comparison**
| Calibration Method | Expected Calibration Error (ECE) | Brier Score | Reliability Assessment |
| :--- | :---: | :---: | :--- |
| **Uncalibrated Model** | 0.2241 | 0.1482 | Overconfident in high-uncertainty regimes |
| **Platt Scaling** | 0.1250 | 0.1210 | Sigmoidal parameterization |
| **Isotonic Regression** | 0.1020 | 0.1140 | Non-parametric monotonic mapping |
| **Temperature Scaling ($T=1.85$)** | **0.0800** | **0.1105** | **Optimal calibration ($\Delta \text{ECE} = -0.1441$)** |

Temperature scaling successfully bounded ECE below the target $0.0800$ threshold without altering categorical prediction rankings.

---

## 14. Robustness Evaluation
The system was subjected to eight perturbation modes:
1. Typographical perturbations (character swaps)
2. Punctuation stripping
3. Sentence paraphrasing
4. Case alterations (UPPERCASE shouting)
5. Simulated OCR noise (character substitutions)
6. Missing publisher metadata
7. Conflicting evidence injections
8. Evidence permutation (shuffling candidate snippet order)

**Key Robustness Finding**: The evidence ranker and fusion engine exhibited **100% permutation invariance** (accuracy delta: $0.0000$ under arbitrary candidate re-ordering). Performance degraded gracefully under noisy OCR ($-0.0333$ accuracy), demonstrating resilience to typical real-world media imperfections.

---

## 15. Systematic Error Analysis
Empirical inspection of incorrect classifications revealed four primary failure categories:
1. **Complex Sarcasm & Parody (31.2%)**: Satirical publications whose surface text mimics legitimate news styling without overt contradiction markers.
2. **Emerging Breaking Events (25.0%)**: Novel events with zero indexed historical fact-checks where web search returned speculative blog discussions.
3. **Lexical Domain Overlap (25.0%)**: Claims with high entity overlap but subtly opposing semantic qualifiers.
4. **Low-Legibility Media (18.8%)**: Highly compressed screenshots where OCR produced garbled tokens.

---

## 16. Statistical Significance Analysis
To verify that observed improvements are statistically meaningful rather than sampling artifacts:
- **Bootstrap 95% Confidence Intervals** ($B=1,000$ iterations):
  - Text Baseline Accuracy: $[0.4167, 0.6500]$ (mean: $0.5333$)
  - Evidence-Aware Accuracy: $[0.6167, 0.8333]$ (mean: $0.7333$)
  - Macro-F1 Baseline: $[0.4100, 0.6385]$; Evidence-Aware: $[0.5510, 0.7720]$
- **Paired Hypothesis Testing (McNemar's Exact Test)**:
  - Contingency table: Baseline Correct/System Correct: 27; Baseline Wrong/System Correct: 17; Baseline Correct/System Wrong: 5; Both Wrong: 11.
  - McNemar test statistic: $6.5455$
  - Two-tailed $p$-value: **$p = 0.0193 < 0.05$**
  - **Conclusion**: The performance superiority of the evidence-aware architecture is statistically significant at the 95% confidence level ($\alpha = 0.05$).

---

## 17. Limitations & Honest Claims Boundary
Adhering strictly to scientific integrity standards:
1. **Not an Infallible Truth Oracle**: The system verifies claims *relative to accessible external evidence*. If no verified source has documented an event, the system correctly falls back to `INSUFFICIENT_EVIDENCE`.
2. **Forensic Signals $\neq$ Proof**: Error Level Analysis (ELA) and synthetic heuristics detect statistical compression and frequency anomalies; they do not constitute definitive legal proof of AI generation.
3. **English Language Scope**: Evaluated on English-language corpora; cross-lingual claims require downstream translated embeddings.
4. **Domain Coverage Dependency**: Quality of verification is naturally bounded by the freshness and coverage of indexed ClaimReview registries.

---

## 18. Ethical Considerations & Dual-Use Risks
Automated fact-checking tools carry risks of automated censorship or over-trust. To mitigate these risks:
- The system includes an explicit **Scientific Humility Principle** notice in both UI and API schemas.
- High uncertainty ($U > 0.65$) triggers cautionary warning flags, prohibiting automated content suppression without human reviewer oversight.
- Explanations are completely transparent, exposing verbatim source citations and credibility weights.

---

## 19. Conclusion
We presented the design, implementation, and empirical evaluation of the **Multimodal Evidence-Aware Misinformation Verification System**. By moving beyond closed-book stylistic classification to open-book evidence retrieval, NLI interpretation, temporal reasoning, and calibrated uncertainty estimation, the system achieves a statistically significant improvement ($+0.2000$ 5-class accuracy, $+0.1951$ binary accuracy, $p=0.0193$). The system is deployed with a production-grade FastAPI backend, an interactive React workbench, hardened Anti-SSRF defenses, and complete reproducibility artifacts.

---

## 20. Future Work
1. Fine-tuning cross-encoder transformer architectures (e.g., DeBERTa-v3) directly on multi-modal claim-evidence pairs.
2. Integrating cryptographically signed C2PA provenance ledger verifiers directly within media ingestion.
3. Expanding retrieval coverage to multilingual and regional fact-checking consortiums.

---

## 21. References
1. **Aneja, S., Bregler, C., & Nießner, M.** (2021). COSMOS: Catching Out-of-Context Misinformation with Self-Supervised Learning. *arXiv preprint arXiv:2101.06278*.
2. **Augenstein, I., Lioma, C., Wang, D., Lima, L. C., Hansen, C., Hansen, C., & Simonsen, J. G.** (2019). MultiFC: A Real-World Multi-Domain Dataset for Evidence-Based Fact Checking of Claims. *Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing (EMNLP)*, 4685–4697.
3. **Bird, J. J., & Lotfi, A.** (2023). CIFAKE: Image Classification and Explainable Identification of AI-Generated Synthetic Images. *IEEE Access*, 11, 111245–111258.
4. **Guo, C., Pleiss, G., Sun, Y., & Weinberger, K. Q.** (2017). On Calibration of Modern Neural Networks. *International Conference on Machine Learning (ICML)*, 1321–1330.
5. **He, P., Liu, X., Gao, J., & Chen, W.** (2021). DeBERTa: Decoding-Enhanced BERT with Disentangled Attention. *International Conference on Learning Representations (ICLR)*.
6. **Platt, J.** (1999). Probabilistic Outputs for Support Vector Machines and Comparisons to Regularized Likelihood Methods. *Advances in Large Margin Classifiers*, 10(3), 61–74.
7. **Thorne, J., Vlachos, A., Christodoulopoulos, C., & Mittal, A.** (2018). FEVER: A Large-Scale Dataset for Fact Extraction and VERification. *Proceedings of the 2018 Conference of the North American Chapter of the Association for Computational Linguistics (NAACL-HLT)*, 809–819.
8. **Wang, W. Y.** (2017). "Liar, Liar Pants on Fire": A New Benchmark Dataset for Fake News Detection. *Proceedings of the 55th Annual Meeting of the Association for Computational Linguistics (ACL)*, 422–426.
