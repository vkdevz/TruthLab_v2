# Multimodal Evidence-Aware Misinformation Verification System

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

A major final-year engineering and scientific research project investigating multimodal evidence-grounded information verification. The system unifies plain text, article URLs, images/screenshots, and videos into a coherent, evidence-retrieval pipeline capable of discerning:
1. **Media Authenticity** (probabilistic visual/audio manipulation indicators)
2. **Claim Veracity** (5-class taxonomy: `SUPPORTED`, `CONTRADICTED`, `MISLEADING`, `OUTDATED`, `INSUFFICIENT_EVIDENCE`)
3. **Contextual & Temporal Integrity** (anachronism and out-of-context recycling detection)
4. **Evidence Sufficiency & Calibration** (epistemic uncertainty estimation with structured audit trails)

---

## Architecture Overview

```mermaid
flowchart LR
    User[Text / URL / Image / Video] --> Ingest[Ingestion Gateway]
    Ingest --> Normalizer[Text / OCR / Whisper ASR]
    Normalizer --> Claims[Atomic Claim Decomposer]
    Claims --> Retrieve[Evidence Retrieval & ClaimReview Cache]
    Retrieve --> NLI[DeBERTa-v3 Stance & Veracity]
    Ingest --> Forensics[Image ELA / ViT Synthetic Probability]
    NLI --> Fusion[Multimodal Evidentiary Fusion]
    Forensics --> Fusion
    Fusion --> Explain[Calibrated Verdict & Audit Trail]
    Explain --> UI[Interactive Verification Workbench]
```

---

## Directory Layout

```
.
├── backend/
│   └── app/
│       ├── api/v1/         # Endpoints & routing
│       ├── core/           # Configuration & security settings
│       ├── db/             # SQLAlchemy async models & migrations
│       ├── ml/             # ML inference pipelines (NLI, Claim, Forensics, Fusion)
│       ├── schemas/        # Pydantic v2 domain schemas
│       └── services/       # Ingestion, scraping, storage, task runners
├── frontend/               # Vite + React (TypeScript) verification workbench
├── docs/                   # Full research, architecture, experiment, and paper docs
│   ├── research/           # Problem formulation, taxonomy, literature survey
│   ├── architecture/       # Detailed component designs and data flows
│   ├── experiments/        # Controlled benchmark logs and ablation records
│   └── paper/              # LaTeX thesis / paper source
├── tests/                  # Automated pytest test suites
└── pyproject.toml          # Python package definitions
```

---

## Quickstart

### 1. Backend Setup
```bash
# Recommended: Create and activate a Python 3.12 venv
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Run test suite
pytest tests/

# Start FastAPI development server
uvicorn backend.app.main:app --reload --port 8000
```
Interactive API documentation: `http://localhost:8000/api/v1/docs`

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Verification Workbench UI: `http://localhost:5173`

---

## Research Publications & Reproducibility
- [Problem Formulation](docs/research/problem_formulation.md)
- [5-Class Veracity Taxonomy](docs/research/taxonomy_definition.md)
- [Evaluation Protocol](docs/research/evaluation_protocol.md)
- [Literature Matrix & Dataset Licensing](docs/research/literature_matrix.md)
