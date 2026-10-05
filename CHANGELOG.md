# Changelog

All notable changes to the **Multimodal Evidence-Aware Misinformation Verification System** are documented in this file.

The project adheres strictly to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v1.0.0-final] - 2026-10-05

### Major Milestones & Release Summary
Final release marking the completion of all 25 research, engineering, and infrastructure milestones. The system is verified as an end-to-end multimodal evidence-aware verification platform capable of verifying claims across Text, URLs, Images, and Video with calibrated uncertainty, transparent audit trails, and hardened security protections.

### Added
- **Reproducible Experimentation Suite** (`research/`):
  - Deterministic random seeds ($S=42$), environment metadata capture, hardware telemetry recording.
  - Benchmarks: Text Baseline (TF-IDF+LR), Evidence-Aware System, Hybrid Retrieval, Progressive Ablation, Temporal Reasoning, Multimodal Evaluation, Media Forensics, Calibration, Uncertainty, Robustness, Error Analysis, and Statistical Significance.
- **Dataset Pipeline & Quality Audit** (`DATASETS.md`, `DATASET_AUDIT.md`):
  - 60-sample 5-class balanced evaluation corpus (12 per class).
  - 0 duplicates, 0 train/test leakages, 0 malformed records.
- **Uncertainty & Calibration Engine** (`backend/app/ml/explainability/uncertainty_layer.py`):
  - Epistemic vs. aleatoric uncertainty decomposition.
  - Normalized Shannon entropy calculation.
  - Temperature scaling ($T=1.85$) reducing ECE from $0.2241$ to $0.0800$.
- **Hardened Security Defenses** (`docs/security.md`):
  - Anti-SSRF gateway with DNS pre-resolution, CIDR blocklist (RFC 1918, CGNAT `100.64.0.0/10`, link-local, cloud metadata), and port whitelist.
  - Magic byte file signature validation (JPEG, PNG, WebP, BMP, MP4, WebM, AVI, QuickTime).
  - Path traversal scrubbing and UUIDv4 storage isolation.
  - Subprocess safety with parameter arrays and execution timeouts.
  - HTTP defense-in-depth response headers.
- **Interactive Verification Workbench** (`frontend/`):
  - Modality flows for Plain Text, URL, Image/Screenshot/Meme, and Video.
  - Real-time progress stepper, zero dummy counters, real loading and error states.
  - Uncertainty telemetry indicators and Scientific Humility Principle notice banner.
  - Filterable evidence citation list by stance (All, Supports, Refutes, Neutral) with NLI marginal distributions.
- **Production Infrastructure & Documentation**:
  - Hardened Dockerfile with non-root user `appuser:10001`, `HEALTHCHECK` directive.
  - `docker-compose.yml` with logging limits and resource quotas.
  - `.dockerignore` and `.env.example`.
  - Comprehensive 21-section academic research paper (`docs/paper/RESEARCH_PAPER.md`).
  - Examiner-focused viva defense guide (`docs/VIVA_PREPARATION.md`).
- **Automated Test Suite**:
  - Expanded from 68 tests to **121 automated tests** across all modules with 100% pass rate.

### Changed
- Standardized project identity: **Multimodal Evidence-Aware Misinformation Verification System**.
- Unified `FullVerificationResponse` schema across all modalities to expose calibrated uncertainty scores and actionability flags.
- Updated version tags to `1.0.0`.

---

## [v0.2-phase2-multimodal-intelligence] - 2026-10-04

### Added
- Image intelligence: EXIF extraction, Error Level Analysis (ELA), frequency synthetic indicators.
- Image OCR text extraction and text normalization.
- Video intelligence: Technical FFmpeg container probe, Whisper ASR speech transcription.
- Video keyframe sampling and onscreen chyron OCR.
- Temporal verifier decoupling event dates from publication dates.
- Multimodal late-fusion engine with evidentiary refutation dominance.
- Interactive verification workbench frontend.
- 68 automated unit and integration tests.

---

## [v0.1-phase1-core-verification] - 2026-10-04

### Added
- Core modular monolith backend using FastAPI and async SQLite.
- URL ingestion with basic Anti-SSRF constraints.
- Atomic claim decomposition and check-worthiness gating.
- Composite evidence retriever querying local ClaimReview indices and web sources.
- Hybrid evidence ranker (TF-IDF cosine + domain credibility weights).
- NLI stance interpretation (SUPPORTS, REFUTES, NEUTRAL).
- 5-class verdict engine (`SUPPORTED`, `CONTRADICTED`, `MISLEADING`, `OUTDATED`, `INSUFFICIENT_EVIDENCE`).
- Directed evidence graph generation and structured audit trails.
- Initial test suite (53 tests).
