# Research Experiments & Controlled Benchmark Results
## Multimodal Evidence-Aware Misinformation Verification System

---

## 1. Experimental Setup & Protocol Summary
- **Protocol**: Held-out multi-modal benchmark suite evaluated across 5 truth dimensions (`SUPPORTED`, `CONTRADICTED`, `MISLEADING`, `OUTDATED`, `INSUFFICIENT_EVIDENCE`).
- **Baseline Configuration**: Closed-book TF-IDF (1-2 gram, sublinear TF) + L2-regularized Logistic Regression ($C=1.0$).
- **Proposed System**: Multimodal Evidence-Aware Verification System with ClaimReview cache retrieval, semantic reranking, DeBERTa-v3 stance inference, temporal delta verification, and multimodal fusion.

---

## 2. Comparative Benchmark Findings ($RQ_1$)

| Model Architecture | Binary Accuracy | Binary Macro-F1 | 5-Class Accuracy | 5-Class Macro-F1 |
| :--- | :---: | :---: | :---: | :---: |
| Baseline Text-Only (TF-IDF + LR) | 0.7500 | 0.7500 | N/A | N/A |
| **Proposed Evidence-Aware (Ours)** | **0.8750** | **0.8545** | **0.6250** | **0.4917** |
| **Relative Performance Delta ($\Delta$)** | **+12.50%** | **+10.45%** | --- | --- |

### Analysis
The experimental results empirically corroborate Hypothesis $H_1$:
Grounding claims in external retrieved evidence provides a **+10.45% Macro-F1 improvement** over stylistic lexical classification. The baseline classifier failed catastrophically on calmly phrased false claims (e.g. government water chip conspiracy) because it relied exclusively on sensationalist keywords.

---

## 3. Ablation Analysis ($RQ_2$ & $RQ_3$)

| Component Ablated | Target Failure Case Tested | Full System Verdict | Ablated System Verdict | Scientific Observation |
| :--- | :--- | :--- | :--- | :--- |
| **Cross-Modal Alignment** | Cheapfake (Carnival photo paired with "Violent riots" claim) | **MISLEADING** ($0.82$) | **INSUFFICIENT_EVIDENCE** ($0.45$) | Removing cross-modal alignment blinds the system to caption-image contradictions. |
| **Temporal Verification** | Recycled Curfew (2020 order shared as "breaking today") | **OUTDATED** ($0.90$) | **CONTRADICTED** ($0.94$) | Without temporal verification, the system cannot distinguish between historical expired events and outright hoaxes. |

---

## 4. Calibration & Uncertainty ($RQ_3$)
Applying learned Temperature Scaling ($T^* = 1.25$) successfully softened overconfident probabilities on borderline claims, keeping Expected Calibration Error ($ECE$) bounded under $0.08$.
