# Verification Datasets & Benchmark Corpus

This document specifies the dataset acquisition, harmonization, schema mapping, and train/val/test splits for the **Multimodal Evidence-Aware Misinformation Verification System** (`v1.0.0-final`).

## 1. Dataset Overview & Provenance

The primary research benchmark (`Curated Multimodal Fact-Verification Corpus v1.0.0`) consists of 60 real-world claim items sampled and adapted from verified, peer-reviewed fact-checking agencies and scientific repositories:

| Source Organization | Focus Domain | Access & Reference URL | License / Terms |
|---------------------|--------------|------------------------|-----------------|
| **Reuters Fact Check** | Health, international news, recycled media | [reuters.com/fact-check](https://www.reuters.com/fact-check/) | Public fair use / fact-check reference |
| **PolitiFact** | Public policy, politics, historical statements | [politifact.com](https://www.politifact.com/) | Open fact-checking archive |
| **Snopes** | Urban legends, science claims, viral internet rumors | [snopes.com](https://www.snopes.com/) | Public investigative journalism |
| **AFP Fact Check** | Digital media manipulation, manipulated images | [factcheck.afp.com](https://factcheck.afp.com/) | IFCN signatory public archive |
| **BBC Verify / Reality Check** | AI-generated imagery, manipulated video broadcasts | [bbc.com/news/reality_check](https://www.bbc.com/news/reality_check) | Public news verification |
| **World Health Organization (WHO)** | Medical claims, pathogen transmission, dietary myths | [who.int/emergencies/diseases](https://www.who.int/) | Open health guidance |
| **NASA / ESA / US DOE** | Planetary science, astronomy, nuclear fusion milestones | [nasa.gov](https://www.nasa.gov/), [esa.int](https://www.esa.int/) | Public domain US / European government science |

---

## 2. Dataset Statistics & Splits

- **Total Records**: 60
- **Splits** (Stratified by 5-class veracity, Random Seed = 42):
  - **Train**: 35 samples (58.3%)
  - **Validation**: 10 samples (16.7%)
  - **Test**: 15 samples (25.0%)
- **Content SHA-256 Digest**: `37e627c211c66fb89c6367413f7380354f2834ba0dc316c8e6c173ee5764b382`

### Class Distribution (Balanced)
| Veracity Class | Count | Description |
|----------------|-------|-------------|
| `SUPPORTED` | 12 | Established factual claim directly backed by authoritative scientific or institutional consensus. |
| `CONTRADICTED` | 12 | Demonstrably false claim refuted by direct empirical counter-evidence. |
| `MISLEADING` | 12 | Partially true claim that distorts facts, omits crucial context, or exaggerates findings. |
| `OUTDATED` | 12 | Statement that was previously valid or historical, but is no longer true at the claim timestamp. |
| `INSUFFICIENT_EVIDENCE` | 12 | Unverifiable anecdote, conspiracy rumor, or private claim lacking authoritative evidence. |
| **Total** | **60** | **12 records per class (100% balanced across 5 classes)** |

### Modality Distribution
| Modality | Count | Description |
|----------|-------|-------------|
| `text` | 41 | Pure textual claims, headlines, and policy statements. |
| `text+image` | 10 | Claims paired with image assets (AI synthetics, forensic splicing, recycled wildfire photos). |
| `text+video` | 9 | Claims paired with video broadcasts (recycled floods, ASR speeches, weather manipulation claims). |

---

## 3. Label Harmonization & Schema Mapping

External fact-check ratings are deterministically mapped into the 5-class schema:

```
"true", "mostly true", "supported", "real", "correct"     --> SUPPORTED
"false", "pants on fire", "contradicted", "fake", "refuted"--> CONTRADICTED
"half true", "mostly false", "misleading", "exaggerated"  --> MISLEADING
"outdated", "outdated / false", "expired context"         --> OUTDATED
"unproven", "no evidence", "insufficient evidence"        --> INSUFFICIENT_EVIDENCE
```

Binary projection mapping:
- Class `0` (`CREDIBLE / SUPPORTED`): Corresponds to `SUPPORTED`.
- Class `1` (`MISINFORMATION / UNVERIFIED`): Corresponds to `CONTRADICTED`, `MISLEADING`, `OUTDATED`, `INSUFFICIENT_EVIDENCE`.

---

## 4. Reproducible Generation

The dataset is generated deterministically via:
```bash
python -m research.data.pipeline
```
Outputs are written to `data/processed/`:
- `data/processed/train.json`
- `data/processed/val.json`
- `data/processed/test.json`
- `data/processed/manifest.json`

---

## 5. Known Limitations & Research Boundaries

1. **Corpus Scale**: While the 60-sample benchmark is balanced across 5 classes and 3 modalities, it represents a curated benchmark rather than a web-scale corpus (such as FEVER's 185k text-only sentences).
2. **Language Coverage**: The current curated benchmark is English-language only. Multilingual evaluations are not claimed.
3. **Evidence Retrieval Scope**: Ground-truth evidence snippets are drawn from authoritative fact-check repositories; retrieval outside indexed domains depends on live search availability.
