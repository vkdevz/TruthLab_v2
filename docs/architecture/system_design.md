# Target System Architecture & Component Design
## Multimodal Evidence-Aware Misinformation Verification System

---

## 1. Modular Monolith Architecture

The system is organized into decoupled layers operating within a unified Python/TypeScript monorepo. This design eliminates microservice overhead, inter-service network latency, and deployment complexity while maintaining strict domain boundaries.

```mermaid
graph TD
    subgraph Client ["Frontend (Vite + React 18 + TypeScript)"]
        UI_Drop[Multimodal Ingestion Dropzone]
        UI_Workbench[Verification Workbench]
        UI_Graph[Interactive Evidence Graph]
        UI_Forensics[Forensic Signal Inspector]
        UI_Export[Audit Trail & Citation Exporter]
    end

    subgraph Gateway ["FastAPI Gateway & Ingestion Layer"]
        API_Router["/api/v1 (REST / Async Job Polling)"]
        Sanitizer[SSRF & MIME Sniffing Validator]
        JobManager[Async Job Lifecycle Tracker]
    end

    subgraph IngestionWorkers ["Multimodal Extractors"]
        TextWorker[Text & URL Normalizer - Trafilatura]
        ImageWorker[OCR Engine - EasyOCR]
        VideoWorker[FFmpeg Scene Extract + Whisper ASR]
    end

    subgraph IntelligenceCore ["Evidence-Grounded Verification Engine"]
        ClaimEngine[Atomic Proposition Decomposer & Check-worthiness]
        RetrievalEngine[Dual-Mode Evidence Retriever: ClaimReview + Web]
        Reranker[Cross-Encoder Semantic Passage Reranker]
        ContextEngine[Temporal Anchor & Geolocation Consistency]
        ForensicsEngine[ELA Compression Variance + ViT Synthetic Probability]
        NLIEngine[DeBERTa-v3 Stance & Entailment Classifier]
    end

    subgraph DecisionLayer ["Calibration & Decision Engine"]
        FusionModel[Multimodal Evidentiary Fusion Matrix]
        Calibrator[Temperature Scaling ECE Minimizer]
        Explainer[Evidence Graph Builder & Citation Formatter]
    end

    subgraph StorageLayer ["Persistence & Cache"]
        DB[(SQLite / DuckDB Persistent Store)]
        ClaimCache[(Local ClaimReview Fact-Check Cache)]
        VectorIndex[(sqlite-vec / Chroma Semantic Index)]
    end

    UI_Drop --> API_Router
    API_Router --> Sanitizer
    Sanitizer --> JobManager
    JobManager --> IngestionWorkers

    IngestionWorkers --> ClaimEngine
    ClaimEngine --> RetrievalEngine
    RetrievalEngine --> ClaimCache
    RetrievalEngine --> VectorIndex
    RetrievalEngine --> Reranker

    Reranker --> NLIEngine
    Reranker --> ContextEngine
    ImageWorker --> ForensicsEngine

    NLIEngine --> FusionModel
    ContextEngine --> FusionModel
    ForensicsEngine --> FusionModel

    FusionModel --> Calibrator
    Calibrator --> Explainer
    Explainer --> DB
    Explainer --> UI_Workbench
    Explainer --> UI_Graph
    Explainer --> UI_Forensics
```

---

## 2. Component Boundaries & Responsibilities

| Subsystem | Primary Python Module | Input | Output | Key Tech |
| :--- | :--- | :--- | :--- | :--- |
| **Ingestion Gateway** | `backend.app.services.scraper` | URL, raw text, uploaded files | Sanitized text / media scratch file | `trafilatura`, `httpx`, `python-magic` |
| **Job Manager** | `backend.app.services.job_manager` | Task invocation | Job UUID, progress state, error handling | `asyncio`, `sqlite` |
| **Claim Intelligence** | `backend.app.ml.claim` | Unified text corpus | List of check-worthy atomic propositions | `spacy`, `transformers` |
| **Evidence Retrieval** | `backend.app.services.retrieval` | Formulated queries | Top-$k$ ranked evidence passages | Google Fact Check API, Tavily, `sqlite-vec` |
| **NLI & Stance** | `backend.app.ml.nli` | (Claim, Evidence) pairs | Entailment / Contradiction logits | `cross-encoder/nli-deberta-v3-base` |
| **Temporal Verification** | `backend.app.ml.context` | Claim date, Evidence dates | Temporal mismatch delta, `OUTDATED` flag | `dateparser`, `python-dateutil` |
| **Image Forensics** | `backend.app.ml.image` | Image bitmap | ELA error map, EXIF tags, synthetic probability | `easyocr`, `pillow`, `torch` |
| **Video Intelligence** | `backend.app.ml.video` | MP4 video | Transcript, Key-frames, Video OCR | `ffmpeg-python`, `scenedetect`, `whisper` |
| **Evidence Fusion** | `backend.app.ml.fusion` | Stance, Temporal, Forensics | Calibrated 5-class verdict | Decision matrix, Logistic meta-learner |
| **Audit Explainer** | `backend.app.ml.explainability` | Fusion verdict & citations | Structured audit JSON, Evidence graph | `networkx`, Pydantic v2 |
