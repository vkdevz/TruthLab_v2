# Systematic Error Analysis & Failure Taxonomy

- **Total Evaluated Claims (Test Set)**: 15
- **Total Misclassifications**: 3
- **System Accuracy**: 80.0%

## 1. Failure Category Breakdown

| Failure Category | Count | Percentage | Description |
|------------------|-------|------------|-------------|
| `TEMPORAL_FAILURE` | 3 | 100.0% | Temporal verifier failed to resolve outdated recycling or misjudged event occurrence vs publication date. |

## 2. Empirical Failure Cases & Root Cause Analysis

### Case 1: [claim_out_004] TEMPORAL_FAILURE
- **Claim**: "Recycled video shows airport flooding disaster happening today in Florida during hurricane season."
- **Modality**: `text+video`
- **Gold Verdict**: `OUTDATED` | **Predicted**: `CONTRADICTED`
- **Confidence**: 0.934 (Uncertainty: `LOW`)
- **Root Cause**: Temporal verifier assigned status 'OUTDATED' rather than recognizing historical event recycling.
- **Remediation**: Enhance temporal anchor extraction for relative temporal phrases and expand historical event knowledge graphs.

### Case 2: [claim_out_007] TEMPORAL_FAILURE
- **Claim**: "Notice: World Health Organization officially warns against taking ibuprofen for COVID-19 symptoms."
- **Modality**: `text`
- **Gold Verdict**: `OUTDATED` | **Predicted**: `CONTRADICTED`
- **Confidence**: 0.934 (Uncertainty: `LOW`)
- **Root Cause**: Temporal verifier assigned status 'HISTORICAL' rather than recognizing historical event recycling.
- **Remediation**: Enhance temporal anchor extraction for relative temporal phrases and expand historical event knowledge graphs.

### Case 3: [claim_out_003] TEMPORAL_FAILURE
- **Claim**: "Urgent alert: Postal service issues warning about anthrax spores found in office mailboxes today!"
- **Modality**: `text`
- **Gold Verdict**: `OUTDATED` | **Predicted**: `CONTRADICTED`
- **Confidence**: 0.934 (Uncertainty: `LOW`)
- **Root Cause**: Temporal verifier assigned status 'OUTDATED' rather than recognizing historical event recycling.
- **Remediation**: Enhance temporal anchor extraction for relative temporal phrases and expand historical event knowledge graphs.

