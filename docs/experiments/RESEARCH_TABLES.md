# Master Research Benchmark Tables

All metrics compiled deterministically from machine-readable experiment results in `research/results/`.

## Table 1: Dataset Statistics & Modalities

| Metric / Attribute | Count / Value | Proportion (%) |
| --- | --- | --- |
| Total Verified Samples | 60 | 100.0% |
| Train Partition | 35 | 58.3% |
| Validation Partition | 10 | 16.7% |
| Test Partition | 15 | 25.0% |
| Class: SUPPORTED | 12 | 20.0% |
| Class: CONTRADICTED | 12 | 20.0% |
| Class: MISLEADING | 12 | 20.0% |
| Class: OUTDATED | 12 | 20.0% |
| Class: INSUFFICIENT_EVIDENCE | 12 | 20.0% |
| Modality: Text Only | 41 | 68.3% |
| Modality: Text + Image | 10 | 16.7% |
| Modality: Text + Video | 9 | 15.0% |
| Class Balance Entropy | 2.3219 | Max: 2.322 |


## Table 2: Text Baseline vs. Proposed Evidence System

| Evaluation Metric | Text Baseline (TF-IDF+LR) | Proposed Evidence System | Relative Delta (Δ) |
| --- | --- | --- | --- |
| Binary Accuracy | 0.8667 | 1.0 | +0.2885 |
| Binary Macro-F1 | 0.7115 | 1.0 | +0.2885 |
| 5-Class Accuracy | 0.5333 | 0.8 | +0.2667 |
| 5-Class Macro-F1 | 0.5276 | 0.7333 | +0.2057 |
| Insufficient Evidence Recall | 0.3333 | 1.0 | +0.6667 |


## Table 3: Progressive Component Ablation

| Configuration | Active Components | 5-Class Acc | 5-Class Macro-F1 | Binary Macro-F1 | SUPPORTED F1 | CONTRADICTED F1 | OUTDATED F1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Configuration A | TF-IDF, Logistic Regression | 0.5333 | 0.5276 | 0.7205 | 0.5714 | 0.4 | 0.6667 |
| Configuration B | Claim Decomposition, Evidence Retrieval... | 0.8 | 0.7333 | 1.0 | 1.0 | 0.6667 | 0.0 |
| Configuration C | Claim Decomposition, Evidence Retrieval... | 0.8 | 0.7333 | 1.0 | 1.0 | 0.6667 | 0.0 |
| Configuration D | Claim Decomposition, Evidence Retrieval... | 0.8 | 0.7333 | 1.0 | 1.0 | 0.6667 | 0.0 |
| Configuration E | Claim Decomposition, Evidence Retrieval... | 0.8 | 0.7333 | 1.0 | 1.0 | 0.6667 | 0.0 |


## Table 4: Confidence Calibration

| Calibration Method | Expected Calibration Error (ECE) | Max Calibration Error (MCE) | Brier Score | ECE Reduction (Δ) |
| --- | --- | --- | --- | --- |
| Uncalibrated | 0.1441 | 0.2484 | 0.0251 | Baseline |
| Temperature Scaling | 0.0 | 0.0 | 0.0 | -0.1441 |
| Platt Scaling | 0.0946 | 0.4767 | 0.0269 | -0.0495 |
| Isotonic Regression | 0.0443 | 0.2649 | 0.0076 | -0.0998 |


## Table 5: System Robustness Under Perturbations

| Perturbation Mode | Accuracy | Macro-F1 | Stability Ratio | F1 Delta (Δ) |
| --- | --- | --- | --- | --- |
| Clean Baseline | 0.4 | 0.28 | 1.0 | 0.0 |
| Spelling Noise | 0.4 | 0.28 | 1.0 | 0.0 |
| Punctuation Distortion | 0.4 | 0.28 | 1.0 | 0.0 |
| Capitalization Distortion | 0.4 | 0.28 | 1.0 | 0.0 |
| Noisy Ocr Simulation | 0.4 | 0.28 | 1.0 | 0.0 |
| Partial Truncation 50Pct | 0.4 | 0.28 | 1.0 | 0.0 |
| Missing Evidence Zero Retrieval | 0.2 | 0.0667 | 0.2 | -0.2133 |
| Conflicting Evidence Injected | 0.4 | 0.28 | 1.0 | 0.0 |
| Reordered Evidence Shuffled | 0.4 | 0.28 | 1.0 | 0.0 |


## Table 6: Multimodal Intelligence & Cross-Modal Alignment

| Pipeline Variant | 5-Class Accuracy | 5-Class Macro-F1 | Binary Accuracy | Disparities Flagged |
| --- | --- | --- | --- | --- |
| Without Multimodal Signals (Text+Evidence) | 0.7895 | 0.7333 | 1.0 | 0 |
| With Multimodal Signals (Forensics+Alignment) | 0.6842 | 0.6167 | 1.0 | 8 |


## Table 7: Failure Taxonomy Breakdown

| Failure Category | Error Count | Percentage (%) | Primary Operational Impact |
| --- | --- | --- | --- |
| TEMPORAL_FAILURE | 3 | 100.0% | Misjudged historical event anchor |


