# Database Schema & Data Models
## Multimodal Evidence-Aware Misinformation Verification System

---

## 1. Relational Schema Architecture

The persistence layer uses SQLite (via `aiosqlite` and `SQLAlchemy 2.0 Async`) for the modular monolith. It provides ACID transactions, zero external server processes, and high-speed local caching.

```mermaid
erDiagram
    VERIFICATION_JOBS ||--o{ CLAIMS_LOG : extracts
    VERIFICATION_JOBS {
        string id PK "UUID-v4"
        string input_modality "TEXT | URL | IMAGE | VIDEO"
        text raw_input_summary "Sanitized excerpt of user input"
        string status "PENDING | PROCESSING | COMPLETED | FAILED"
        int progress_percent "0 to 100"
        string current_stage "Pipeline stage indicator"
        text error_message "Nullable error description"
        json result_payload "Serialized FullVerificationResponse"
        datetime created_at
        datetime updated_at
        datetime completed_at
    }

    CLAIMS_LOG {
        string id PK "UUID-v4"
        string job_id FK "References verification_jobs.id"
        text raw_text "Sentence fragment extracted"
        text canonical_claim "Normalized atomic proposition"
        float checkworthy_score "0.0 to 1.0"
        boolean is_checkworthy "Threshold boolean"
        string veracity_verdict "SUPPORTED | CONTRADICTED | etc."
        float confidence "Calibrated certainty"
        string temporal_anchor "Extracted event date string"
        datetime created_at
    }

    EVIDENCE_CACHE {
        string id PK "UUID-v4"
        string query_hash "SHA256 of search query"
        text query_text "Query formulated for search"
        string source_name "Publisher or Portal name"
        text source_url "Direct URL citation"
        string domain "Indexed domain for credibility lookup"
        text snippet_text "Passage excerpt"
        float retrieval_score "Semantic similarity score"
        string stance "SUPPORTS | REFUTES | NEUTRAL"
        boolean is_claim_review "ClaimReview flag"
        datetime cached_at "Cache timestamp (TTL 24h)"
    }
```

---

## 2. Indices & Performance Optimization

1. **`verification_jobs.id`**: Primary Key (UUIDv4) for $O(1)$ async polling queries.
2. **`claims_log.job_id`**: B-tree index for efficient batch retrieval of all claims linked to a verification job.
3. **`evidence_cache.query_hash`**: SHA-256 hash index preventing redundant external API calls for duplicate claims across sessions.
4. **`evidence_cache.domain`**: B-tree index enabling instantaneous domain reputation lookups.
