# Multimodal Evidence-Aware Misinformation Verification System

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-8.3-646cff.svg)](https://vitejs.dev/)
[![Tests](https://img.shields.io/badge/tests-53%20passed-brightgreen.svg)]()
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

A major final-year engineering and scientific research project investigating multimodal evidence-grounded information verification. The system unifies plain text, article URLs, images/screenshots, and videos into a coherent, evidence-retrieval pipeline capable of discerning:
1. **Media Authenticity** (probabilistic visual/audio manipulation indicators)
2. **Claim Veracity** (5-class taxonomy: `SUPPORTED`, `CONTRADICTED`, `MISLEADING`, `OUTDATED`, `INSUFFICIENT_EVIDENCE`)
3. **Contextual & Temporal Integrity** (anachronism and out-of-context recycling detection)
4. **Evidence Sufficiency & Calibration** (epistemic uncertainty estimation with structured audit trails)

---

## Phase 1 Status: COMPLETED

Phase 1 delivers a fully working, tested, and integrated:
**TEXT / URL → CLAIM → EVIDENCE → VERIFICATION → EXPLANATION** pipeline.

- [x] Strict Anti-SSRF URL Ingestion & Article Extraction
- [x] Atomic Claim Extraction & Decomposition with Check-worthiness Filtering
- [x] Pluggable Evidence Provider Abstraction (`LocalClaimReviewProvider`, `GoogleFactCheckProvider`, `CompositeEvidenceRetriever`)
- [x] Hybrid Evidence Ranking (TF-IDF + Cosine Similarity + Credibility Weights + ClaimReview Provenance)
- [x] NLI Evidence Stance Interpretation (`SUPPORTS`, `REFUTES`, `NEUTRAL`)
- [x] Deterministic 5-Class Verdict Engine with Documented Category Precedence
- [x] Evidence Sufficiency Gating ($S(\mathcal{E}) < \tau_{\text{sufficient}} \to \text{INSUFFICIENT\_EVIDENCE}$)
- [x] Structured Explanation Layer (Reasoning Summaries, Citations, System Limitations, Evidence Graph)
- [x] Classical Text Baseline Pipeline (TF-IDF + Logistic Regression, logged in `docs/experiments/baseline_results.json`)
- [x] Async SQLite Persistence & Job Tracking (`/api/v1/verification/{id}`)
- [x] 53/53 Automated Tests Passing

---

## Architecture Overview

```mermaid
flowchart LR
    User[Text / URL / Image / Video] --> Ingest[Ingestion Gateway + Anti-SSRF]
    Ingest --> Normalizer[Text / Trafilatura Extraction]
    Normalizer --> Claims[Atomic Claim Decomposer & Checkworthiness]
    Claims --> Retrieve[Composite Evidence Retriever]
    Retrieve --> Rank[Hybrid Evidence Ranker]
    Rank --> NLI[NLI Stance Interpreter]
    NLI --> Verdict[5-Class Verdict Engine & Sufficiency Gate]
    Verdict --> Explain[Calibrated Verdict + Evidence Graph + Audit Trail]
    Explain --> UI[Interactive Verification Workbench]
```

---

## Directory Layout

```
.
├── backend/
│   └── app/
│       ├── api/v1/         # Endpoints & routing (verify/text, verify/url, verification/{id})
│       ├── core/           # Configuration & security settings
│       ├── db/             # SQLAlchemy async models & SQLite persistence
│       ├── evidence/       # Abstract EvidenceProvider, ranking, composite retriever
│       ├── ingestion/      # Anti-SSRF URLValidator and text normalizer
│       ├── ml/             # Claim decomposer, checkworthiness, NLI, forensics
│       ├── repositories/   # Async CRUD repository for verification records
│       ├── schemas/        # Pydantic v2 domain schemas
│       └── services/       # Pipeline service orchestrator & job manager
├── frontend/               # Vite + React (TypeScript) verification workbench (Port 5175)
├── data/                   # Reference ClaimReview and benchmark datasets
├── docs/                   # Complete research, architecture, experiment, and API docs
│   ├── architecture.md     # Modular monolith architecture specifications
│   ├── verification-pipeline.md # Complete verification pipeline data flow
│   ├── datasets.md         # Documented datasets, splits, and baseline findings
│   ├── api.md              # API endpoint documentation
│   └── experiments/        # Actual measured latency and baseline metric logs
├── scripts/                # Data preparation and pipeline profiling scripts
├── tests/                  # 53 automated unit and integration tests
└── pyproject.toml          # Python package definitions
```

---

## Quickstart

### 1. Backend Setup
```bash
# Recommended: Create and activate Python 3.12 venv
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Run complete test suite (53 tests)
PYTHONPATH=. pytest tests/

# Start FastAPI development server
uvicorn backend.app.main:app --reload --port 8000
```
Interactive API documentation: `http://localhost:8000/api/v1/docs`

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev -- --port 5175
```
Verification Workbench UI: `http://localhost:5175`

---

## Reproducible Research Baseline & Benchmarks

Run the text baseline training and evaluation:
```bash
PYTHONPATH=. python3 backend/app/ml/baseline/train_baseline.py
```
- In-Domain Train Metrics: Accuracy: 1.000, Macro F1: 1.000, ECE: 0.399
- Out-of-Domain Test Metrics: Accuracy: 0.700, Precision: 0.750, Recall: 0.600, Macro F1: 0.697, ECE: 0.184
- Metrics logged to: `docs/experiments/baseline_results.json`

Run pipeline latency profiling:
```bash
PYTHONPATH=. python3 scripts/profile_pipeline.py
```
- Latency profile logged to: `docs/experiments/pipeline_latency.json`

---

## Documentation Links
- [System Architecture](docs/architecture.md)
- [Verification Pipeline](docs/verification-pipeline.md)
- [API Reference](docs/api.md)
- [Dataset Documentation](docs/datasets.md)
- [Database Schema](docs/architecture/database_schema.md)
