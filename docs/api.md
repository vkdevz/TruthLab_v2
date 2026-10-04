# API Reference Documentation (Phase 1)

Base URL: `http://localhost:8000/api/v1`

Interactive OpenAPI / Swagger UI: `http://localhost:8000/api/v1/docs`

---

## 1. System Health

### `GET /health`
Returns system status, service name, and active version.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "Multimodal Evidence-Aware Misinformation Verification System",
  "version": "0.1.0"
}
```

---

## 2. Text Verification

### `POST /verify/text`
Accepts raw text or paragraphs, performs decomposition, retrieves evidence, and returns an explainable veracity assessment.

**Request Body:**
```json
{
  "text": "The Indian Ministry of Communications has officially banned all 5G network services nationwide."
}
```

**Response (200 OK):**
```json
{
  "job_id": "2ddf0519-cdc0-469c-b539-6c334d474ab5",
  "created_at": "2026-10-04T06:47:36.171051Z",
  "completed_at": "2026-10-04T06:47:36.180305Z",
  "input_modality": "TEXT",
  "overall_veracity": "OUTDATED",
  "overall_confidence": 0.90,
  "claims_verified": [
    {
      "claim": {
        "id": "c-df1fd1b0",
        "raw_text": "The Indian Ministry of Communications has officially banned all 5G network services nationwide",
        "canonical_claim": "The Indian Ministry of Communications has officially banned all 5G network services nationwide",
        "checkworthy_score": 0.72,
        "is_checkworthy": true,
        "entities": ["The Indian Ministry", "Communications"],
        "temporal_anchor": null,
        "search_queries": ["..."]
      },
      "veracity": "OUTDATED",
      "confidence": 0.90,
      "evidence_sufficiency_score": 2.72,
      "is_temporal_mismatch": false,
      "evidence_items": [
        {
          "id": "loc-3-d5bfd1",
          "source_name": "PolitiFact",
          "source_url": "https://www.politifact.com/factchecks/2020/mar/state-curfew-lockdown/",
          "domain": "politifact.com",
          "domain_credibility_weight": 1.6,
          "snippet_text": "...",
          "retrieval_score": 0.85,
          "stance": "REFUTES",
          "stance_probabilities": {"SUPPORTS": 0.03, "REFUTES": 0.92, "NEUTRAL": 0.05},
          "is_claim_review": true,
          "claim_review_rating": "Outdated / False"
        }
      ],
      "audit": {
        "summary": "...",
        "supporting_citations": ["..."],
        "refuting_citations": ["..."],
        "limitations": ["..."]
      }
    }
  ],
  "evidence_graph": {
    "nodes": [{"id": "node-c-df1fd1b0", "label": "...", "type": "claim", "status": "OUTDATED"}],
    "edges": [{"source": "node-loc-3-d5bfd1", "target": "node-c-df1fd1b0", "relation": "REFUTES", "weight": 0.85}]
  },
  "executive_summary": "The content recirculates historical events or obsolete announcements presented out of their original temporal context.",
  "system_limitations": [
    "Verification is grounded strictly in indexed fact-checking corpora and authoritative public web sources available at query time.",
    "NLI and stance scoring represent probabilistic evidence interpretation, not absolute infallible ground truth."
  ]
}
```

---

## 3. URL Verification (with Anti-SSRF Protection)

### `POST /verify/url`
Accepts a target web page or news article URL, validates against private/loopback IP addresses, extracts article text safely, and executes verification.

**Request Body:**
```json
{
  "url": "https://www.reuters.com/business/telecom-5g-update"
}
```

**Error Responses:**
- `400 Bad Request`: When URL targets `localhost`, `127.0.0.1`, private IP subnet, unsupported scheme (`file://`, `ftp://`), or exceeds redirect limit.
- `413 Payload Too Large`: When HTML page exceeds 5 MB.
- `422 Unprocessable Entity`: When page contains insufficient readable text.

---

## 4. Verification Job Retrieval

### `GET /verification/{job_id}`
Retrieves the persistent verification record, execution stage, progress percentage, and full result payload by ID.

**Response (200 OK):**
```json
{
  "job_id": "2ddf0519-cdc0-469c-b539-6c334d474ab5",
  "input_modality": "TEXT",
  "status": "COMPLETED",
  "progress_percent": 100,
  "current_stage": "FINISHED",
  "error_message": null,
  "result": { ... },
  "created_at": "2026-10-04T06:47:36.167655",
  "completed_at": "2026-10-04T06:47:36.180357"
}
```
