# System Architecture & Technical Specifications (Phase 1)

## 1. Architectural Philosophy: Modular Monolith

The system is designed as a **modular monolith** optimized for scientific rigor, maintainability, and solo-developer throughput. Rather than introducing distributed microservices with unnecessary network RPC overhead and operational complexity, all modules communicate via well-defined in-process Python interfaces and typed Pydantic schemas.

```
backend/
├── app/
│   ├── api/             # FastAPI v1 routing and endpoint controllers
│   ├── core/            # Configuration management (Pydantic Settings) & security
│   ├── db/              # Async SQLAlchemy models & SQLite/Postgres sessions
│   ├── evidence/        # Abstract EvidenceProvider, ranking, and composite retriever
│   ├── ingestion/       # Strict Anti-SSRF URLValidator and TextIngestionService
│   ├── ml/              # Claim decomposer, checkworthiness, NLI, forensics
│   ├── repositories/    # Async CRUD repository for jobs, claims, and cache
│   ├── schemas/         # Immutable Pydantic v2 domain schemas
│   ├── services/        # Orchestrator pipeline, job manager, and scrapers
│   └── main.py          # FastAPI application factory and lifespan hooks
```

---

## 2. Core Subsystems

### A. Ingestion Gateway
- **Anti-SSRF Protection**: Every URL submitted to `/api/v1/verify/url` undergoes DNS resolution via `socket.getaddrinfo`. Resolved IPv4/IPv6 addresses are checked against IETF private, loopback, link-local, and reserved CIDR ranges.
- **Safe Network Limits**: 8.0-second HTTP timeout, maximum 3 redirect hops with hop-by-hop re-validation, 5 MB maximum response size, and `text/html` MIME type enforcement.
- **Content Normalization**: Raw text submissions undergo Unicode NFKC normalization, whitespace collapse, and length boundary checking (min 5, max 25,000 characters).

### B. Claim Intelligence Layer
- **Conjunction Decomposition**: Multi-clause statements are decomposed using boundary regexes into atomic propositions.
- **Check-worthiness Gate**: Heuristic and rule-based scorer evaluates factual indicators, named entity density, and numerical metrics while penalizing purely subjective opinions and rhetorical queries.
- **Query Generation**: Synthesizes search query variants for multi-angle evidence retrieval.

### C. Evidence Engine & Provider Abstraction
- **`EvidenceProvider` Interface**: Isolates external search and fact-checking APIs behind an abstract contract.
- **`LocalClaimReviewProvider`**: High-speed, deterministic offline index of verified IFCN ClaimReview records, supporting Jaccard and containment matching for reproducible evaluation.
- **`GoogleFactCheckProvider`**: Live integration querying the Google Fact Check Tools API with graceful network fallback.
- **`CompositeEvidenceRetriever`**: Multi-provider aggregator that collects, unifies, and deduplicates evidence items by canonical URL.

### D. Evidence Ranking & NLI Stance Interpretation
- **`HybridEvidenceRanker`**: Combines sublinear TF-IDF unigram/bigram cosine similarity, source reputation multipliers, and ClaimReview provenance boosts.
- **`NLIEvidenceInterpreter`**: Maps evidence passages to the 3-class relation (`SUPPORTS`, `REFUTES`, `NEUTRAL`). Distinguishes evidentiary interpretation from absolute ground truth.

### E. Five-Class Verdict Engine & Sufficiency Gate
- **Sufficiency Gate**: Computes $S(\mathcal{E}) = \sum (\text{retrieval\_score} \times \text{domain\_credibility})$. If $S(\mathcal{E}) < \tau_{\text{sufficient}}$, the engine returns `INSUFFICIENT_EVIDENCE` without ungrounded speculation.
- **Documented Precedence Rules**:
  1. `INSUFFICIENT_EVIDENCE`: Evidentiary support below threshold.
  2. `OUTDATED`: Historical notices or expired regulations recirculated in present context.
  3. `CONTRADICTED`: Weighted refutation ratio $\ge 0.60$. Max confidence capped at 0.96.
  4. `SUPPORTED`: Weighted corroboration ratio $\ge 0.65$. Max confidence capped at 0.96.
  5. `MISLEADING`: Geographic recontextualization, partial truths, or conflicting evidence balance.

### F. Persistence Layer
- Async SQLite database (`verification.sqlite3`) managed via SQLAlchemy `AsyncSession`.
- Persists full `VerificationJobRecord` entries, atomic claims, and cached evidence.

### G. Media Ingestion & Security Gateway
- MIME and magic byte signature verification (`storage.py`) for JPEG, PNG, WebP, MP4, WebM, and MOV containers.
- Sanitized filenames, UUIDv4 storage keys, and streaming size limits (15MB image, 100MB video).
- Safe temporary file lifecycle and guaranteed cleanup.

### H. Image Intelligence Subsystem
- **Metadata & Provenance**: EXIF, dimensions, color space, camera software, and C2PA provenance indicators.
- **Error Level Analysis (ELA)**: Recompression differential analysis emitting structured `manipulation_signal`.
- **Synthetic Detector Interface**: `SyntheticMediaDetector` probabilistic frequency analyzer emitting model version, preprocessing, and uncertainty.
- **OCR Engine**: Bounded text digitization and regex-based artifact normalizer feeding the claim pipeline.

### I. Video Intelligence Subsystem
- **Technical Probe**: FFmpeg container analysis (duration <= 300s, resolution, fps, audio presence).
- **Speech ASR**: Modular `VideoTranscriber` (Whisper base.en integration) preserving timestamped dialogue segments.
- **Keyframe Extraction & Scene OCR**: Bounded keyframe sampling extracting onscreen chyrons, tickers, and visual forensics.

### J. Temporal & Context Verifier
- Explicit decoupling of event occurrence dates from source publication dates.
- Heuristic recency/breaking marker analysis for out-of-context recycling detection (`OUTDATED`).
- Geographic entity consistency matching returning `UNKNOWN` where context cannot be determined.

### K. Multimodal Late-Fusion Engine
- Transparent late fusion combining evidence sufficiency, stance support/refute, temporal penalties, media manipulation scores, and cross-modal alignment.
- Strict precedence: Evidentiary refutation dominance ensures authoritative external evidence dominates weak media indicators.
- Cross-modal disparity checker detects "cheapfakes" (real visual media with contradicting captions).
