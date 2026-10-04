# Verification Taxonomy Specification
## Multimodal Evidence-Aware Misinformation Verification System

---

## 1. Executive Summary

Standard academic datasets and commercial tools frequently reduce verification to binary classifications:
- $\text{Class } 0$: Real / Legitimate
- $\text{Class } 1$: Fake / False

This binary framing is scientifically invalid for real-world information ecosystems. Real-world misinformation rarely consists of 100% fabricated statements; it predominantly features cherry-picked statistics, out-of-context genuine imagery, unverified rumors, and outdated facts repackaged as breaking news.

This system establishes a **5-Class Veracity & Evidence Taxonomy**:
1. `SUPPORTED`
2. `CONTRADICTED`
3. `MISLEADING`
4. `OUTDATED`
5. `INSUFFICIENT_EVIDENCE`

---

## 2. Taxonomy Definitions & Operational Rules

### 2.1 SUPPORTED
- **Formal Definition**: The factual core of the claim is directly corroborated by high-credibility, authoritative, or primary sources retrieved during verification. Furthermore, accompanying media shows no evidence of deceptive manipulation or contextual mismatch.
- **Operational Criteria**:
  - Aggregated NLI Support Score: $\bar{p}_{\text{entail}} \ge 0.70$
  - Aggregated NLI Refutation Score: $\bar{p}_{\text{contradict}} < 0.20$
  - Evidence Sufficiency Score: $S(\mathcal{E}) \ge \tau_{\text{sufficient}}$
  - Temporal Mismatch: None detected ($I_{\text{outdated}} = 0$)
  - Media Authenticity: Synthetic probability $p_{\text{synthetic}} < 0.40$
- **Representative Example**: 
  - *Claim*: "The James Webb Space Telescope detected carbon dioxide in an exoplanet atmosphere."
  - *Evidence*: Peer-reviewed NASA/ESA publication confirming $CO_2$ spectroscopic detection in WASP-39b.
  - *Verdict*: **SUPPORTED**.

### 2.2 CONTRADICTED
- **Formal Definition**: The factual assertion is explicitly refuted, falsified, or proven impossible by authoritative consensus, primary evidence, or reputable fact-checking investigations.
- **Operational Criteria**:
  - Aggregated NLI Refutation Score: $\bar{p}_{\text{contradict}} \ge 0.65$
  - OR direct match with a `False` / `Pants on Fire` rating in verified ClaimReview records.
  - Evidence Sufficiency: $S(\mathcal{E}) \ge \tau_{\text{sufficient}}$
- **Representative Example**:
  - *Claim*: "The World Health Organization confirmed bananas cure malaria."
  - *Evidence*: WHO scientific advisory clarifying no dietary cure exists for plasmodium infection.
  - *Verdict*: **CONTRADICTED**.

### 2.3 MISLEADING
- **Formal Definition**: The content contains a mixture of factual elements and false inferences, selective omission of critical context, deceptive editing, exaggerated claims, or genuine media paired with false captions ("cheapfakes").
- **Operational Criteria**:
  - *Condition A (Cherry-picking/Mixed Stance)*: Both support and refutation scores exist ($p_{\text{entail}} \ge 0.35$ and $p_{\text{contradict}} \ge 0.35$).
  - *Condition B (Cross-Modal Mismatch)*: Visual media is genuine, but textual claims assert an unrelated event or identity.
  - *Condition C (Synthetic Media without Disclaimer)*: $p_{\text{synthetic}} \ge 0.75$ presented as breaking documentary evidence.
- **Representative Example**:
  - *Claim*: "Crime rates doubled in City X overnight" (accompanying genuine photo of police cars).
  - *Evidence*: Official statistics show crime grew 2% year-over-year; photo is from a routine training drill in 2021.
  - *Verdict*: **MISLEADING**.

### 2.4 OUTDATED
- **Formal Definition**: The factual event, quotation, or data point was historically accurate at the time of occurrence, but is no longer valid, has been superseded by new events/laws, or is being falsely presented as current.
- **Operational Criteria**:
  - Historical Entailment: $\bar{p}_{\text{entail}} \ge 0.65$ for the historical event.
  - Temporal Delta: $\Delta_t = |t_{\text{current}} - t_{\text{event}}| > \tau_{\text{outdated}}$ (e.g. $> 180$ days).
  - Linguistic Framing: Contains present-tense or urgency markers ("breaking now", "today", "yesterday", "urgent alert").
- **Representative Example**:
  - *Claim*: "Curfew announced across the city; schools closed tomorrow."
  - *Evidence*: Notice was issued during the March 2020 COVID lockdowns; no active curfew exists in 2026.
  - *Verdict*: **OUTDATED**.

### 2.5 INSUFFICIENT_EVIDENCE
- **Formal Definition**: The retrieval pipeline cannot locate sufficient, authoritative, or reliable external evidence to corroborate or refute the claim with statistical confidence.
- **Operational Criteria**:
  - Evidence Sufficiency Metric: $S(\mathcal{E}) < \tau_{\text{sufficient}}$
  - OR retrieved sources have low domain credibility / high conflicting noise.
  - OR the input constitutes subjective opinion, aesthetic preference, or future prediction rather than an empirical claim.
- **Representative Example**:
  - *Claim*: "My neighbor's private company will release an anti-gravity car next December."
  - *Evidence*: Zero indexed news reports, filings, or fact-checks exist.
  - *Verdict*: **INSUFFICIENT_EVIDENCE**.

---

## 3. Boundary & Disambiguation Matrix

| Claim Characteristic | Primary Stance | Media State | Temporal State | Assigned Verdict |
| :--- | :--- | :--- | :--- | :--- |
| Verified true, contemporaneous | Supports ($\ge 0.70$) | Clean / Natural | Current ($\Delta_t \approx 0$) | **SUPPORTED** |
| Factually disproven by consensus | Refutes ($\ge 0.65$) | Any | Any | **CONTRADICTED** |
| True event, but happened 4 years ago presented as today | Supports historical | Natural | Obsolete ($\Delta_t \gg 0$) | **OUTDATED** |
| Partial truth with missing context | Mixed (Both $\ge 0.35$) | Natural | Current | **MISLEADING** |
| Genuine photo + fabricated narrative ("cheapfake") | Refutes claim-photo link | Genuine photo | Misattributed | **MISLEADING** |
| Highly realistic AI deepfake presented as real news | N/A or Unverified | Synthetic ($\ge 0.75$) | Current | **MISLEADING** |
| Obscure claim with zero reliable web citations | Undetermined | Any | Any | **INSUFFICIENT_EVIDENCE** |
| Pure subjective opinion ("Movie X is the worst in history") | Non-factual | Any | Any | **INSUFFICIENT_EVIDENCE** |

---

## 4. Scientific Justification for Thesis & Viva Defense

1. **Failure of Naive Classifiers**: Traditional classifiers classify "schools closed due to hurricane" as `Real` because the grammar and lexical style resemble authentic disaster reporting, ignoring that the hurricane occurred 8 years ago.
2. **Epistemic Humility**: A verification system that asserts "Real" or "Fake" on unindexed rumors loses credibility. Outputting `INSUFFICIENT_EVIDENCE` models the standard practice of professional journalistic organizations (e.g., AFP, Snopes, PolitiFact, Full Fact).
3. **Continuous Probability for Media**: Treating AI image and audio detection as probabilistic signals integrated into a multi-factor decision tree prevents catastrophic false accusations caused by JPEG compression or camera noise.
