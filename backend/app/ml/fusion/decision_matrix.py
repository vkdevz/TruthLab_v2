from backend.app.schemas.veracity import VeracityLabel
from backend.app.schemas.fusion import FusionFeatureVector, FusionDecision
from backend.app.core.config import settings


def _normalize_distribution(target_label: str, target_prob: float, secondary_weights: dict[str, float]) -> dict[str, float]:
    p = round(float(target_prob), 3)
    rem = max(0.0, 1.0 - p)
    total_sec = sum(secondary_weights.values()) or 1.0
    dist = {target_label: p}
    for k, w in secondary_weights.items():
        if k != target_label:
            dist[k] = round(rem * (w / total_sec), 3)
    diff = round(1.0 - sum(dist.values()), 3)
    if diff != 0:
        sec_keys = [k for k in dist if k != target_label]
        if sec_keys:
            best_sec = max(sec_keys, key=lambda k: dist[k])
            dist[best_sec] = round(dist[best_sec] + diff, 3)
    return dist


class MultimodalDecisionMatrix:
    """Late-fusion decision engine synthesizing stance scores, temporal penalties,
    media manipulation probabilities, and cross-modal alignment into a single coherent verdict.
    Evidence-grounded verification remains the primary principle: strong textual evidence
    dominates weak media signals."""

    def resolve(self, features: FusionFeatureVector, notes: list[str] | None = None) -> FusionDecision:
        rationale = list(notes or [])

        # 1. Direct refutation dominance
        # Authoritative evidence directly contradicts the factual assertion
        if features.stance_refute_score >= settings.STANCE_REFUTE_THRESHOLD:
            rationale.append("Authoritative evidence consensus refutes the claim (evidentiary refutation dominance).")
            conf = round(min(0.96, 0.65 + 0.30 * features.stance_refute_score), 3)
            return FusionDecision(
                final_verdict=VeracityLabel.CONTRADICTED,
                confidence=conf,
                verdict_distribution=_normalize_distribution(
                    "CONTRADICTED", conf,
                    {"MISLEADING": 0.70, "SUPPORTED": 0.10, "OUTDATED": 0.10, "INSUFFICIENT_EVIDENCE": 0.10}
                ),
                dimension_scores={
                    "refute_score": features.stance_refute_score,
                    "support_score": features.stance_support_score,
                    "sufficiency": features.evidence_sufficiency,
                },
                fusion_rationale=rationale,
            )

        # 2. Cross-modal mismatch or severe media tampering ("cheapfake" / visual contradiction)
        if features.cross_modal_alignment < 0.70 or features.media_manipulation_score > 0.75:
            rationale.append("Cross-modal contradiction or significant visual tampering detected paired with claim.")
            conf = round(min(0.92, max(0.78, 0.75 + 0.15 * (1.0 - features.cross_modal_alignment))), 3)
            return FusionDecision(
                final_verdict=VeracityLabel.MISLEADING,
                confidence=conf,
                verdict_distribution=_normalize_distribution(
                    "MISLEADING", conf,
                    {"CONTRADICTED": 0.50, "SUPPORTED": 0.30, "OUTDATED": 0.10, "INSUFFICIENT_EVIDENCE": 0.10}
                ),
                dimension_scores={
                    "alignment": features.cross_modal_alignment,
                    "media_manipulation": features.media_manipulation_score,
                    "sufficiency": features.evidence_sufficiency,
                },
                fusion_rationale=rationale,
            )

        # 3. Temporal recycling penalty
        # Claim presents an old event as breaking/current
        if features.temporal_penalty > 0.60:
            rationale.append("Temporal analysis identified historical out-of-context recycling.")
            conf = round(min(0.95, max(0.85, 0.80 + 0.15 * features.temporal_penalty)), 3)
            return FusionDecision(
                final_verdict=VeracityLabel.OUTDATED,
                confidence=conf,
                verdict_distribution=_normalize_distribution(
                    "OUTDATED", conf,
                    {"MISLEADING": 0.50, "SUPPORTED": 0.30, "CONTRADICTED": 0.10, "INSUFFICIENT_EVIDENCE": 0.10}
                ),
                dimension_scores={
                    "temporal_penalty": features.temporal_penalty,
                    "sufficiency": features.evidence_sufficiency,
                },
                fusion_rationale=rationale,
            )

        # 4. Evidence sufficiency gate
        # If evidence is inadequate to make an empirical determination, do not speculate
        if features.evidence_sufficiency < settings.EVIDENCE_SUFFICIENCY_THRESHOLD:
            rationale.append("Evidence retrieval density below minimum statistical sufficiency threshold.")
            conf = round(
                max(0.30, min(0.48, 0.30 + 0.15 * (features.evidence_sufficiency / max(0.01, settings.EVIDENCE_SUFFICIENCY_THRESHOLD)))),
                3
            )
            return FusionDecision(
                final_verdict=VeracityLabel.INSUFFICIENT_EVIDENCE,
                confidence=conf,
                verdict_distribution=_normalize_distribution(
                    "INSUFFICIENT_EVIDENCE", conf,
                    {"MISLEADING": 0.35, "SUPPORTED": 0.25, "CONTRADICTED": 0.25, "OUTDATED": 0.15}
                ),
                dimension_scores={
                    "sufficiency": features.evidence_sufficiency,
                    "alignment": features.cross_modal_alignment,
                    "manipulation": features.media_manipulation_score,
                },
                fusion_rationale=rationale,
            )

        # 5. Direct verification support
        # High corroboration in authoritative evidence; weak media signals do not override strong evidence
        if features.stance_support_score >= settings.STANCE_SUPPORT_THRESHOLD:
            rationale.append("Authoritative evidence corroborates the claim; media context is congruent.")
            conf = round(min(0.96, 0.65 + 0.30 * features.stance_support_score), 3)
            return FusionDecision(
                final_verdict=VeracityLabel.SUPPORTED,
                confidence=conf,
                verdict_distribution=_normalize_distribution(
                    "SUPPORTED", conf,
                    {"MISLEADING": 0.70, "CONTRADICTED": 0.10, "OUTDATED": 0.10, "INSUFFICIENT_EVIDENCE": 0.10}
                ),
                dimension_scores={
                    "support_score": features.stance_support_score,
                    "alignment": features.cross_modal_alignment,
                    "sufficiency": features.evidence_sufficiency,
                },
                fusion_rationale=rationale,
            )

        # 6. Genuine conflicting / polarized stance balance
        if features.stance_support_score >= 0.25 and features.stance_refute_score >= 0.25:
            rationale.append("Evidence is conflicting across polarized sources.")
            ambig_conf = round(
                min(0.85, max(0.65, 0.60 + 0.20 * (1.0 - abs(features.stance_support_score - features.stance_refute_score)))),
                3
            )
            return FusionDecision(
                final_verdict=VeracityLabel.MISLEADING,
                confidence=ambig_conf,
                verdict_distribution=_normalize_distribution(
                    "MISLEADING", ambig_conf,
                    {"SUPPORTED": 0.40, "CONTRADICTED": 0.40, "OUTDATED": 0.10, "INSUFFICIENT_EVIDENCE": 0.10}
                ),
                dimension_scores={
                    "support_score": features.stance_support_score,
                    "refute_score": features.stance_refute_score,
                    "sufficiency": features.evidence_sufficiency,
                },
                fusion_rationale=rationale,
            )

        # 7. Non-committal or neutral evidence lacking polarized stance mass
        rationale.append("Available evidence is neutral or non-committal, lacking sufficient stance polarity to verify or refute.")
        conf = round(
            max(0.30, min(0.48, 0.30 + 0.15 * (features.evidence_sufficiency / max(0.01, settings.EVIDENCE_SUFFICIENCY_THRESHOLD)))),
            3
        )
        return FusionDecision(
            final_verdict=VeracityLabel.INSUFFICIENT_EVIDENCE,
            confidence=conf,
            verdict_distribution=_normalize_distribution(
                "INSUFFICIENT_EVIDENCE", conf,
                {"MISLEADING": 0.35, "SUPPORTED": 0.25, "CONTRADICTED": 0.25, "OUTDATED": 0.15}
            ),
            dimension_scores={
                "sufficiency": features.evidence_sufficiency,
                "support_score": features.stance_support_score,
                "refute_score": features.stance_refute_score,
            },
            fusion_rationale=rationale,
        )


decision_matrix = MultimodalDecisionMatrix()


