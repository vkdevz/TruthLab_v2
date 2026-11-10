# TruthLab: Priority Issues Matrix & Remediation Log

This document tracks all identified defects, security vulnerabilities, architectural inconsistencies, and calibration deficits across TruthLab_v2, prioritized by operational severity and research impact.

---

## Severity Classification Framework

- **P0 — Critical**: Security vulnerabilities, fake or stubbed functionality, severe data corruption, or broken API contracts.
- **P1 — High**: Architecture duplication, logic drift, uncalibrated heuristic scores, or SSRF defense gaps.
- **P2 — Medium**: Performance bottlenecks, deprecation warnings, unreferenced helper modules, or missing runtime timeouts.
- **P3 — Low**: Documentation discrepancies, stylistic nits, or non-blocking logging enhancements.

---

## 1. Prioritized Issues Summary Table

| Issue ID | Severity | Category | Component | Status | Verification |
| :--- | :---: | :--- | :--- | :---: | :--- |
| **ISSUE-01** | `P0` | Fake Functionality | `backend/app/api/v1/endpoints/ingest.py` | **FIXED** | `tests/test_codebase_hardening_and_unification.py` |
| **ISSUE-02** | `P0` | Security (SSRF) | `backend/app/services/scraper.py` | **FIXED** | `tests/test_codebase_hardening_and_unification.py` |
| **ISSUE-03** | `P1` | Architecture Duplication | `backend/app/ml/nli/stance_classifier.py` | **FIXED** | `tests/test_codebase_hardening_and_unification.py` |
| **ISSUE-04** | `P1` | Architecture Duplication | `backend/app/ml/nli/veracity_scorer.py` | **FIXED** | `tests/test_codebase_hardening_and_unification.py` |
| **ISSUE-05** | `P1` | Architecture Duplication | `backend/app/services/retrieval/reranker.py` | **FIXED** | `tests/test_codebase_hardening_and_unification.py` |
| **ISSUE-06** | `P1` | Uncalibrated Constants | `backend/app/verification/verdict_engine.py` | **FIXED** | `tests/test_verification_engine.py` |
| **ISSUE-07** | `P1` | Probability Normalization | `backend/app/ml/fusion/decision_matrix.py` | **FIXED** | `tests/test_codebase_hardening_and_unification.py` |
| **ISSUE-08** | `P0` | Security: Path Disclosure | `backend/app/api/v1/endpoints/ingest.py` | **FIXED** | `tests/test_codebase_hardening_and_unification.py` |
| **ISSUE-09** | `P1` | Uncorroborated Stance Bias| `backend/app/evidence/provider.py` | **FIXED** | `tests/test_codebase_hardening_and_unification.py` |
| **ISSUE-10** | `P1` | Multimodal Late Fusion Bypass | `backend/app/api/v1/endpoints/image.py` | **FIXED** | `tests/test_image_intelligence.py` |
| **ISSUE-11** | `P2` | Redundant HTTP Roundtrips | `backend/app/services/pipeline_service.py` | **FIXED** | `tests/test_codebase_hardening_and_unification.py` |
| **ISSUE-12** | `P2` | Library Deprecation | `research/experiments/forensics_benchmark.py` | **FIXED** | `tests/test_forensics_benchmark.py` |
| **ISSUE-13** | `P2` | Incomplete Integration | `backend/app/ml/explainability/audit_generator.py`| **CATALOGED**| Architecture documentation & planned roadmap |
| **ISSUE-14** | `P2` | Research Methodology | `research/experiments/calibration_experiments.py`| **DOCUMENTED**| Methodology notes in Audit Report |
| **ISSUE-15** | `P2` | Frontend Cascading Render | `frontend/src/App.tsx` | **FIXED** | `npm run lint` (0 warnings) |
| **ISSUE-16** | `P3` | Documentation Drift | `README.md` temperature constant notation | **DOCUMENTED**| Temperature documentation harmonized |
| **ISSUE-17** | `P0` | Fatal TypeError in Video Forensics | `backend/app/ml/fusion/cross_modal_alignment.py` | **FIXED** | `tests/test_adversarial_audit.py` |
| **ISSUE-18** | `P1` | Neutral Evidence Routed to MISLEADING | `backend/app/ml/fusion/decision_matrix.py` | **FIXED** | `tests/test_adversarial_audit.py` |
| **ISSUE-19** | `P1` | NLI Topical Overlap Hallucinated SUPPORTS | `backend/app/verification/nli.py` | **FIXED** | `tests/test_adversarial_audit.py` |
| **ISSUE-20** | `P1` | Neutral Evidence Gate Bypass via Low-Mass Citation | `backend/app/verification/verdict_engine.py` | **FIXED** | `tests/test_adversarial_audit.py` |
| **ISSUE-21** | `P1` | Multi-Claim Aggregation Declared Unproven Dominated as SUPPORTED | `backend/app/services/pipeline_service.py` | **FIXED** | `tests/test_adversarial_audit.py` |
| **ISSUE-22** | `P1` | Date Parser Truncated Full Dates to Jan 1st | `backend/app/ml/context/temporal_parser.py` | **FIXED** | `tests/test_adversarial_audit.py` |
| **ISSUE-23** | `P2` | Residual Fabricated p-values in Research Docs & UI | `docs/`, `frontend/src/components/ResearchBenchmarkTable.tsx` | **FIXED** | Frontend build & research sync |

---

## 2. Detailed Issue Reports & Remediation Details

### ISSUE-01: Ingestion API Endpoint Used Stub Dummy Processor (`process_dummy_job`)
- **Severity**: `P0 — Critical`
- **Component**: `backend/app/api/v1/endpoints/ingest.py`
- **Description**: The `/ingest/text`, `/ingest/url`, and `/ingest/media` endpoints returned `PENDING` job tokens, but the background task executed `process_dummy_job()`. This routine simply slept through 25% and 75% steps before marking the job completed with a hardcoded dictionary. Clients polling `/jobs/{job_id}` never received an actual verification result.
- **Root Cause**: An early prototyping stub was preserved without being connected to `pipeline_service`.
- **Remediation**: Replaced `process_dummy_job` with authentic asynchronous workers (`execute_text_verification_job`, `execute_url_verification_job`, `execute_media_verification_job`) wired directly to `pipeline_service.verify_text`, `pipeline_service.verify_url`, `pipeline_service.verify_image_path`, and `pipeline_service.verify_video_path`.
- **Regression Test**: Added `test_ingest_executes_real_verification_in_background` in `tests/test_codebase_hardening_and_unification.py`.

---

### ISSUE-02: Legacy Scraper Vulnerable to SSRF Redirect Hops and IPv6 Bypass
- **Severity**: `P0 — Critical`
- **Component**: `backend/app/services/scraper.py`
- **Description**: While `backend/app/ingestion/url_ingest.py` had comprehensive SSRF protections (`URLValidator`), `ScraperService` used a separate, primitive DNS lookup (`socket.gethostbyname`) that did not detect IPv6 loopbacks, cloud metadata CIDRs (`169.254.0.0/16`), or redirect-based SSRF (it configured `httpx.AsyncClient(follow_redirects=True)` without inspecting subsequent target IP addresses).
- **Root Cause**: Divergent code paths between legacy scraping helpers and the Phase 1 secure URL ingestion service.
- **Remediation**: Refactored `ScraperService` to delegate all URL validation directly to `URLValidator.validate_url()` and all fetching to `URLIngestionService.ingest_url()`.
- **Regression Test**: Added `test_scraper_service_hardened_ssrf_blocking` testing cloud metadata, loopback, private subnets, and unsupported schemes.

---

### ISSUE-03: StanceClassifier Duplicated NLIEvidenceInterpreter
- **Severity**: `P1 — High`
- **Component**: `backend/app/ml/nli/stance_classifier.py`
- **Description**: Contained a duplicate implementation of rule-based stance classification with lexical contradiction and entailment cues. It featured a typographical error (`ENTTAILMENT_CUES` with double 'T') and diverged from `NLIEvidenceInterpreter`.
- **Root Cause**: Redundant files created across disparate development sprints.
- **Remediation**: Transformed `StanceClassifier` into an adapter delegating directly to `NLIEvidenceInterpreter`, preserving the legacy method signature `predict_stance` and `evaluate_evidence_stances`.
- **Regression Test**: Added `test_stance_classifier_unification`.

---

### ISSUE-04: VeracityScorer Duplicated FiveClassVerdictEngine
- **Severity**: `P1 — High`
- **Component**: `backend/app/ml/nli/veracity_scorer.py`
- **Description**: Implemented parallel decision logic for the 5-veracity taxonomy with slight discrepancies in confidence scoring and temporal rule handling compared to `verdict_engine.py`.
- **Root Cause**: Split between legacy `/verify/claim` endpoint and the unified pipeline service.
- **Remediation**: Refactored `VeracityScorer.score_claim` to delegate directly to `FiveClassVerdictEngine.evaluate_veracity`.
- **Regression Test**: Added `test_veracity_scorer_unification`.

---

### ISSUE-05: EvidenceReranker Duplicated HybridEvidenceRanker
- **Severity**: `P1 — High`
- **Component**: `backend/app/services/retrieval/reranker.py`
- **Description**: Redundant TF-IDF reranking routines between `EvidenceReranker` and `HybridEvidenceRanker`.
- **Root Cause**: Module duplication across retrieval services and evidence pipeline layers.
- **Remediation**: Refactored `EvidenceReranker.rerank` to delegate to `hybrid_evidence_ranker.rank_evidence`.
- **Regression Test**: Added `test_reranker_unification`.

---

### ISSUE-06 & ISSUE-07: Static Hardcoded Confidence Magic Numbers & Probability Normalization
- **Severity**: `P1 — High`
- **Component**: `backend/app/verification/verdict_engine.py` and `backend/app/ml/fusion/decision_matrix.py`
- **Description**: The system assigned static arbitrary constants (`0.90`, `0.82`, `0.72`, `0.45`) to prediction confidence instead of deriving them continuously from evidentiary sufficiency, stance distribution, and cross-modal alignment. Furthermore, probability distributions did not strictly sum to 1.0.
- **Root Cause**: Placeholder constants left during heuristic decision matrix design.
- **Remediation**: Replaced static values with continuous functions and added exact probability distribution normalization (`_normalize_distribution`) ensuring all 5-class distributions sum to 1.0.
- **Regression Test**: Added `test_decision_matrix_distributions_sum_to_one` in `tests/test_codebase_hardening_and_unification.py`.

---

### ISSUE-08: Internal Filesystem Path Exposure in Media Ingestion
- **Severity**: `P0 — Critical`
- **Component**: `backend/app/api/v1/endpoints/ingest.py`
- **Description**: Endpoint `POST /api/v1/ingest/media` returned `saved_path: str(saved_path)` directly in the JSON response, exposing server local directories and filesystem paths to API consumers (violating Principle 14).
- **Root Cause**: Temporary debugging field inadvertently preserved in production endpoint response.
- **Remediation**: Removed `saved_path` from response payload; replaced with safe sanitized identifier `file_id`.
- **Regression Test**: Added `test_ingest_media_no_internal_path_leak_and_completes_job` in `tests/test_codebase_hardening_and_unification.py`.

---

### ISSUE-09: Uncorroborated Evidence Defaulted to SUPPORTS Bias
- **Severity**: `P1 — High`
- **Component**: `backend/app/evidence/provider.py`
- **Description**: `WikipediaEvidenceProvider` and `PublicWebSearchProvider` previously set snippet stance to `SUPPORTS` with 85% probability whenever no refute or support cues matched.
- **Root Cause**: Inverted fallback condition in heuristic stance assignment.
- **Remediation**: Corrected fallback to `StanceType.NEUTRAL` with 80% neutral probability when neither contradiction nor entailment cues match.
- **Regression Test**: Added `test_evidence_providers_neutral_on_keyword_absence` in `tests/test_codebase_hardening_and_unification.py`.

---

### ISSUE-10: Media Forensics Skipped in Image/Video Claim Verification
- **Severity**: `P1 — High`
- **Component**: `backend/app/api/v1/endpoints/image.py` & `backend/app/ml/video/video_pipeline.py`
- **Description**: Image and video endpoints extracted forensic manipulation indicators (ELA, splicing, synthetic detector) but omitted passing them into `veracity_scorer.score_claim`, bypassing late multimodal fusion.
- **Root Cause**: Incomplete parameter forwarding to `veracity_scorer`.
- **Remediation**: Wired `image_forensics` and `video_forensics` into `veracity_scorer.score_claim`, allowing late fusion matrix to detect cheapfakes and visual tampering.
- **Regression Test**: Verified in `tests/test_image_intelligence.py` and `tests/test_video_intelligence.py`.

---

### ISSUE-11: Duplicate HTTP Roundtrips on Ingest URL
- **Severity**: `P2 — Medium`
- **Component**: `backend/app/api/v1/endpoints/ingest.py` & `backend/app/services/pipeline_service.py`
- **Description**: `/api/v1/ingest/url` fetched article data synchronously and then re-fetched it in the background task.
- **Root Cause**: Lack of preloaded article forwarding.
- **Remediation**: Supported `preloaded_article` in `pipeline_service.verify_url` and forwarded from `ingest_url`.
- **Regression Test**: Verified in `tests/test_codebase_hardening_and_unification.py`.

---

### ISSUE-12: Pillow Image.getdata() Deprecation Warning
- **Severity**: `P2 — Medium`
- **Component**: `research/experiments/forensics_benchmark.py`
- **Description**: Emitted `DeprecationWarning: Image.Image.getdata is deprecated and will be removed in Pillow 14`.
- **Root Cause**: Use of legacy Pillow API to strip EXIF data from synthetic test images.
- **Remediation**: Replaced with `Image.fromarray(np.array(img_pristine))`.
- **Regression Test**: Clean pytest run with 0 deprecation warnings from TruthLab source code.

---

### ISSUE-13: AuditReportGenerator Not Wired to Main Pipeline Service
- **Severity**: `P2 — Medium`
- **Component**: `backend/app/ml/explainability/audit_generator.py`
- **Description**: `AuditReportGenerator` implements clean node-edge graph building and certificate generation, but `pipeline_service.py` manually implemented inline graph generation.
- **Status**: Cataloged for Phase 2 roadmap refactor to eliminate redundant graph assembly code.

---

### ISSUE-14: Calibration Experiment Utilizes Synthetic Beta Distribution Logits
- **Severity**: `P2 — Medium`
- **Component**: `research/experiments/calibration_experiments.py`
- **Description**: Post-hoc temperature scaling benchmark evaluated against simulated beta-distributed random logits rather than end-to-end model logits.
- **Status**: Documented transparently in `AUDIT_REPORT.md` and `RESEARCH_TABLES.md`.

---

### ISSUE-15: Frontend Cascading Render in File Preview
- **Severity**: `P2 — Medium`
- **Component**: `frontend/src/App.tsx`
- **Description**: Calling `setState` synchronously within a `useEffect` on file selection triggered an oxlint React hook warning.
- **Root Cause**: Object URL lifecycle synchronized via effect rather than event handler.
- **Remediation**: Moved preview URL derivation to `handleFileSelect` with clean unmount revocation.
- **Regression Test**: `npm run lint` passes with 0 errors and 0 warnings.

---

### ISSUE-17: Fatal TypeError in Cross-Modal Alignment on Default Video Forensics
- **Severity**: `P0 — Critical`
- **Component**: `backend/app/ml/fusion/cross_modal_alignment.py`
- **Description**: Accessing `video_forensics.synthetic_face_probability > 0.75` without checking `is not None` crashed video verification when no synthetic face was detected (defaulting to `None`).
- **Remediation**: Added `is not None` guard check.
- **Regression Test**: Verified via `test_cross_modal_alignment_handles_none_synthetic_face_probability`.

---

### ISSUE-18: Neutral Evidence Evaluated as MISLEADING in Decision Matrix
- **Severity**: `P1 — High`
- **Component**: `backend/app/ml/fusion/decision_matrix.py`
- **Description**: When evidence was predominantly neutral (low support and low refute scores), Rule 6 treated the lack of polarity as a stance contradiction and output `MISLEADING` with 0.80 confidence.
- **Remediation**: Gated Rule 6 to require active polarized conflict (`support >= 0.25 and refute >= 0.25`); added Rule 7 routing neutral evidence to `INSUFFICIENT_EVIDENCE` ($\le 0.48$).
- **Regression Test**: Verified via `test_decision_matrix_neutral_evidence_routes_to_insufficient_evidence`.

---

### ISSUE-19: NLI Topical Lexical Overlap Erroneously Assigned SUPPORTS
- **Severity**: `P1 — High`
- **Component**: `backend/app/verification/nli.py`
- **Description**: Non-polarized passages sharing 2-3 content words with a claim (e.g., ancient Egyptian pyramid history vs alien construction claims) were marked `SUPPORTS`.
- **Remediation**: Neutralized topic overlap heuristics to default to `NEUTRAL` ($P(\text{NEUTRAL}) = 0.80$).
- **Regression Test**: Verified via `test_nli_interpreter_topical_overlap_is_neutral_not_supports`.

---

### ISSUE-20: Neutral Evidence Gate Bypass via Incidental Low-Mass Citations
- **Severity**: `P1 — High`
- **Component**: `backend/app/verification/verdict_engine.py`
- **Description**: An incidental low-mass citation bypassed the neutral evidence gate, triggering `MISLEADING` via fallback Rule E.
- **Remediation**: Enforced neutral evidence gate whenever active evidence ratio $< 0.25$ or when both support and refute masses $< 0.35$.
- **Regression Test**: Verified via `test_neutral_evidence_does_not_produce_supported_verdict`.

---

### ISSUE-21: Multi-Claim Aggregation Declared Unproven-Dominated Content as SUPPORTED
- **Severity**: `P1 — High`
- **Component**: `backend/app/services/pipeline_service.py`
- **Description**: Articles where unproven claims outnumbered corroborated claims were labeled `SUPPORTED`, accompanied by a false explanation claiming "All propositions are corroborated".
- **Remediation**: Routed unproven-dominated claims to `INSUFFICIENT_EVIDENCE` and updated explanation generation to report corroborated vs unproven claims honestly.
- **Regression Test**: Verified via `test_pipeline_unproven_claims_domination_and_explanation_honesty`.

---

### ISSUE-22: Temporal Parser Truncated Specific Month-Day-Year Dates to Jan 1st
- **Severity**: `P1 — High`
- **Component**: `backend/app/ml/context/temporal_parser.py`
- **Description**: Regex for 4-digit years ran before month-name dates, truncating `"October 15, 2020"` to `"2020-01-01"`, causing false timeline mismatches.
- **Remediation**: Prioritized full date regex parsing and aligned calendar years for year-only anchors.
- **Regression Test**: Verified via `test_temporal_parser_prioritizes_full_date_over_year`.

---

### ISSUE-23: Residual Fabricated p-Values Across Presentation Slides, Viva Prep & Frontend
- **Severity**: `P2 — Medium`
- **Component**: `docs/PRESENTATION_SLIDES.md`, `docs/VIVA_DEMO_SCRIPT.md`, `docs/VIVA_PREPARATION.md`, `frontend/src/components/ResearchBenchmarkTable.tsx`
- **Description**: Legacy claims of $p=0.0193$ and $p=0.031$ remained in non-code documentation and frontend UI cards.
- **Remediation**: Synchronized all documentation and frontend components to true empirical metrics ($N=15$, exact McNemar $p=0.2891$, bootstrap mean delta $+0.2502$).
- **Regression Test**: Clean frontend production build and verification of empirical figures.
