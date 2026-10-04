# Verification Pipeline (Phase 1 & Phase 2)

## End-to-End Multimodal Pipeline Data Flow

The unified Phase 2 workflow executes an integrated multimodal pipeline:

```
TEXT / URL / IMAGE / VIDEO
   ↓ [1. Ingestion, Anti-SSRF & Magic Byte Signature Validation]
Extracted Content: Trafilatura / OCR Normalizer / Whisper ASR
   ↓ [2. Unified Textual Corpus & Forensic Signal Extraction]
Unified Corpus + Image/Video Forensics (EXIF, ELA, Synthetic, Probe)
   ↓ [3. Claim Extraction & Checkworthiness]
Atomic Claims
   ↓ [4. Multi-Provider Evidence Retrieval]
Candidate Evidence Snippets
   ↓ [5. Hybrid Evidence Ranking]
Ranked Top-k Evidence
   ↓ [6. NLI Stance Interpretation]
Evidentiary Stances (SUPPORTS / REFUTES / NEUTRAL)
   ↓ [7. Temporal & Context Analysis]
Temporal Alignment (CURRENT / HISTORICAL / OUTDATED / UNKNOWN)
   ↓ [8. Multimodal Late-Fusion Engine]
Fusion Decision (Refutation Dominance, Cross-Modal Alignment)
   ↓ [9. Verdict Engine & Explanation]
FullVerificationResponse (Verdict + Confidence + Forensics + Audit + Graph)
```

---

## 1. Input Ingestion & Security

1. **Text Ingestion** (`backend/app/ingestion/text_ingest.py`):
   - Normalizes text via Unicode NFKC.
   - Trims extraneous whitespace, tabs, and duplicate newlines.
   - Enforces minimum length (5 chars) and maximum length (25,000 chars).
2. **URL Ingestion** (`backend/app/ingestion/url_ingest.py`):
   - Validates schema (`http` and `https` only).
   - Resolves DNS hostname via `socket.getaddrinfo`.
   - Rejects loopback (`127.0.0.1`, `::1`), private CIDRs (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and link-local ranges.
   - Follows up to 3 redirects, re-validating every redirect target against SSRF rules.
   - Limits response body to 5 MB and verifies `text/html` content type.
   - Extracts readable article text and metadata via Trafilatura.

---

## 2. Claim Intelligence & Decomposition

- **Conjunction Splitting**: Statements containing conjunctions like *"and"*, *"but"*, *"while"*, *"furthermore"* are segmented into distinct propositions.
- **Check-worthiness Filtering**:
  - Drops interrogatives, pure opinions (*"in my opinion"*, *"I feel"*), and short conversational greetings.
  - Scores factual verbs (*"announced"*, *"banned"*, *"reported"*), entity counts, and numeric values.
  - Sets `is_checkworthy = True` if score $\ge 0.60$.
- **Search Query Generation**: Builds specialized keyword query strings for targeted index retrieval.

---

## 3. Evidence Engine & Provider Abstraction

- Abstract `EvidenceProvider` contract:
  ```python
  class EvidenceProvider(ABC):
      @abstractmethod
      async def retrieve(self, query: str, claim_id: str, limit: int = 5) -> list[EvidenceSnippet]: ...
  ```
- **Composite Retriever**:
  - Broadcasts queries to `LocalClaimReviewProvider` and `GoogleFactCheckProvider`.
  - Aggregates returned snippets and deduplicates candidates by `source_url`.

---

## 4. Evidence Ranking

- Implemented in `HybridEvidenceRanker`:
  - Builds TF-IDF unigram and bigram representation across claim and evidence passages.
  - Computes cosine similarity.
  - Applies a 1.5x multiplier to official ClaimReview fact-check records.
  - Weights final score by `domain_credibility_weight` (e.g., 1.8x for official government fact-checks, 1.6x for IFCN signatories).

---

## 5. NLI Claim-Evidence Relationship

- Evaluates the relationship between the claim and the evidence passage:
  - **`REFUTES`**: Evidence passage contains contradiction cues (*"false"*, *"denied"*, *"hoax"*, *"misleading"*).
  - **`SUPPORTS`**: Corroboration cues (*"confirmed"*, *"verified"*, *"announced"*) or high contextual token alignment.
  - **`NEUTRAL`**: Insufficient semantic overlap.
- Assigns probability distribution `{"SUPPORTS": p_s, "REFUTES": p_r, "NEUTRAL": p_n}`.

---

## 6. Five-Class Verdict Engine Logic

1. **Evidence Sufficiency Gate**:
   - Computes $S(\mathcal{E}) = \sum (\text{retrieval\_score} \times \text{credibility\_weight})$.
   - If $S(\mathcal{E}) < 1.0$, returns `INSUFFICIENT_EVIDENCE` with calibrated confidence 0.45.
2. **Precedence Hierarchy**:
   - `OUTDATED`: Triggered if ClaimReview flags obsolete notice or temporal analysis detects past expired notice.
   - `CONTRADICTED`: Triggered if weighted refutation ratio $\ge 0.60$.
   - `SUPPORTED`: Triggered if weighted support ratio $\ge 0.65$.
   - `MISLEADING`: Triggered by geographic recontextualization or contradictory balance between sources.

---

## 7. Multimodal Late-Fusion & Cross-Modal Consistency

When image or video inputs are provided:
1. **Evidentiary Refutation Dominance**:
   - If authoritative fact-check evidence directly refutes the claim ($\ge 0.65$), the verdict resolves to `CONTRADICTED`, regardless of low visual anomaly scores.
2. **Cross-Modal Consistency ("Cheapfake" Detection)**:
   - Evaluates token alignment between the stated caption/claim and visual OCR text extracted from images/keyframes.
   - Contradictory pairs (e.g. caption claiming riots vs chyron showing festival) trigger `MISLEADING` with explicit explanatory notes.
3. **Temporal Outdated Penalty**:
   - Out-of-context historical media recirculated as breaking news triggers `OUTDATED`.

---

## 8. Structured Explanation & Audit Trail

Every verification response returns:
- **`overall_veracity`**: One of the 5 taxonomy classes.
- **`overall_confidence`**: Calibrated probability bounded to avoid false 100% certainty.
- **`claims_verified`**: List of individual atomic claims with evidence snippets and stance probabilities.
- **`evidence_graph`**: Graph nodes and edges representing claims, sources, and stance relationships.
- **`executive_summary`**: Human-readable synthesis of evidence rationale.
- **`system_limitations`**: Explicit boundaries of model capability and knowledge horizons.
