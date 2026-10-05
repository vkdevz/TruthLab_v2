# Systematic Error Analysis & Failure Taxonomy

- **Total Evaluated Claims (Test Set)**: 15
- **Total Misclassifications**: 4
- **System Accuracy**: 73.3%

## 1. Failure Category Breakdown

| Failure Category | Count | Percentage | Description |
|------------------|-------|------------|-------------|
| `TEMPORAL_FAILURE` | 3 | 75.0% | Temporal verifier failed to resolve outdated recycling or misjudged event occurrence vs publication date. |
| `RETRIEVAL_FAILURE` | 1 | 25.0% | Target evidence exists in reality, but retrieval query formulation or lexical mismatch missed the snippet. |

## 2. Empirical Failure Cases & Root Cause Analysis

### Case 1: [claim_ins_012] RETRIEVAL_FAILURE
- **Claim**: "Unverified rumor claims an unnamed space agency detected a metallic obelisk floating near Jupiter's moon Callisto."
- **Modality**: `text`
- **Gold Verdict**: `INSUFFICIENT_EVIDENCE` | **Predicted**: `SUPPORTED`
- **Confidence**: 0.94 (Uncertainty: `LOW`)
- **Root Cause**: Retrieved 1 tangential snippets that falsely inflated evidence sufficiency.
- **Remediation**: Increase strictness of semantic relevance thresholding before admitting snippets to fusion.

### Case 2: [claim_out_004] TEMPORAL_FAILURE
- **Claim**: "Recycled video shows airport flooding disaster happening today in Florida during hurricane season."
- **Modality**: `text+video`
- **Gold Verdict**: `OUTDATED` | **Predicted**: `CONTRADICTED`
- **Confidence**: 0.934 (Uncertainty: `LOW`)
- **Root Cause**: Temporal verifier assigned status 'OUTDATED' rather than recognizing historical event recycling.
- **Remediation**: Enhance temporal anchor extraction for relative temporal phrases and expand historical event knowledge graphs.

### Case 3: [claim_out_007] TEMPORAL_FAILURE
- **Claim**: "Notice: World Health Organization officially warns against taking ibuprofen for COVID-19 symptoms."
- **Modality**: `text`
- **Gold Verdict**: `OUTDATED` | **Predicted**: `CONTRADICTED`
- **Confidence**: 0.934 (Uncertainty: `LOW`)
- **Root Cause**: Temporal verifier assigned status 'HISTORICAL' rather than recognizing historical event recycling.
- **Remediation**: Enhance temporal anchor extraction for relative temporal phrases and expand historical event knowledge graphs.

### Case 4: [claim_out_003] TEMPORAL_FAILURE
- **Claim**: "Urgent alert: Postal service issues warning about anthrax spores found in office mailboxes today!"
- **Modality**: `text`
- **Gold Verdict**: `OUTDATED` | **Predicted**: `CONTRADICTED`
- **Confidence**: 0.934 (Uncertainty: `LOW`)
- **Root Cause**: Temporal verifier assigned status 'OUTDATED' rather than recognizing historical event recycling.
- **Remediation**: Enhance temporal anchor extraction for relative temporal phrases and expand historical event knowledge graphs.

