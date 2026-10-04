from backend.app.schemas.veracity import VeracityLabel
from backend.app.schemas.fusion import FusionFeatureVector, FusionDecision
from backend.app.core.config import settings


class MultimodalDecisionMatrix:
    """Late-fusion decision engine synthesizing stance scores, temporal penalties,
    media manipulation probabilities, and cross-modal alignment into a single coherent verdict."""

    def resolve(self, features: FusionFeatureVector, notes: list[str] | None = None) -> FusionDecision:
        rationale = list(notes or [])

        # 1. Cross-modal mismatch or media tampering ("cheapfake" / visual contradiction)
        if features.cross_modal_alignment <= 0.70 or features.media_manipulation_score > 0.75:
            rationale.append("Cross-modal contradiction or visual manipulation detected paired with claim.")
            return FusionDecision(
                final_verdict=VeracityLabel.MISLEADING,
                confidence=0.82,
                verdict_distribution={
                    "MISLEADING": 0.82,
                    "CONTRADICTED": 0.10,
                    "SUPPORTED": 0.04,
                    "OUTDATED": 0.02,
                    "INSUFFICIENT_EVIDENCE": 0.02,
                },
                dimension_scores={
                    "alignment": features.cross_modal_alignment,
                    "media_manipulation": features.media_manipulation_score,
                },
                fusion_rationale=rationale,
            )

        # 2. Evidence sufficiency check
        if features.evidence_sufficiency < settings.EVIDENCE_SUFFICIENCY_THRESHOLD:
            rationale.append("Evidence retrieval density below minimum statistical threshold.")
            return FusionDecision(
                final_verdict=VeracityLabel.INSUFFICIENT_EVIDENCE,
                confidence=0.45,
                verdict_distribution={
                    "INSUFFICIENT_EVIDENCE": 0.85,
                    "SUPPORTED": 0.03,
                    "CONTRADICTED": 0.04,
                    "MISLEADING": 0.05,
                    "OUTDATED": 0.03,
                },
                dimension_scores={
                    "sufficiency": features.evidence_sufficiency,
                    "alignment": features.cross_modal_alignment,
                    "manipulation": features.media_manipulation_score,
                },
                fusion_rationale=rationale,
            )

        # 2. Temporal recycling penalty
        if features.temporal_penalty > 0.60:
            rationale.append("Temporal analysis identified historical out-of-context recycling.")
            return FusionDecision(
                final_verdict=VeracityLabel.OUTDATED,
                confidence=0.90,
                verdict_distribution={
                    "OUTDATED": 0.88,
                    "MISLEADING": 0.06,
                    "SUPPORTED": 0.03,
                    "CONTRADICTED": 0.02,
                    "INSUFFICIENT_EVIDENCE": 0.01,
                },
                dimension_scores={
                    "temporal_penalty": features.temporal_penalty,
                    "sufficiency": features.evidence_sufficiency,
                },
                fusion_rationale=rationale,
            )

        # 3. Direct refutation dominance
        if features.stance_refute_score >= settings.STANCE_REFUTE_THRESHOLD:
            rationale.append("Authoritative evidence consensus refutes the claim.")
            conf = round(min(0.96, 0.65 + 0.30 * features.stance_refute_score), 3)
            return FusionDecision(
                final_verdict=VeracityLabel.CONTRADICTED,
                confidence=conf,
                verdict_distribution={
                    "CONTRADICTED": conf,
                    "MISLEADING": round((1.0 - conf) * 0.7, 3),
                    "SUPPORTED": 0.02,
                    "OUTDATED": 0.02,
                    "INSUFFICIENT_EVIDENCE": 0.01,
                },
                dimension_scores={
                    "refute_score": features.stance_refute_score,
                    "support_score": features.stance_support_score,
                },
                fusion_rationale=rationale,
            )

        # 4. Cross-modal mismatch or media tampering ("cheapfake" / synthetic manipulation)
        if features.cross_modal_alignment < 0.65 or features.media_manipulation_score > 0.70:
            rationale.append("Cross-modal contradiction or visual manipulation detected paired with claim.")
            return FusionDecision(
                final_verdict=VeracityLabel.MISLEADING,
                confidence=0.82,
                verdict_distribution={
                    "MISLEADING": 0.82,
                    "CONTRADICTED": 0.10,
                    "SUPPORTED": 0.04,
                    "OUTDATED": 0.02,
                    "INSUFFICIENT_EVIDENCE": 0.02,
                },
                dimension_scores={
                    "alignment": features.cross_modal_alignment,
                    "media_manipulation": features.media_manipulation_score,
                },
                fusion_rationale=rationale,
            )

        # 5. Direct verification support
        if features.stance_support_score >= settings.STANCE_SUPPORT_THRESHOLD:
            rationale.append("Authoritative evidence corroborates the claim; media is authentic and contemporaneous.")
            conf = round(min(0.96, 0.65 + 0.30 * features.stance_support_score), 3)
            return FusionDecision(
                final_verdict=VeracityLabel.SUPPORTED,
                confidence=conf,
                verdict_distribution={
                    "SUPPORTED": conf,
                    "MISLEADING": round((1.0 - conf) * 0.6, 3),
                    "CONTRADICTED": 0.02,
                    "OUTDATED": 0.02,
                    "INSUFFICIENT_EVIDENCE": 0.01,
                },
                dimension_scores={
                    "support_score": features.stance_support_score,
                    "alignment": features.cross_modal_alignment,
                },
                fusion_rationale=rationale,
            )

        # 6. Ambiguous / Mixed stance
        rationale.append("Evidence is conflicting or non-conclusive across sources.")
        return FusionDecision(
            final_verdict=VeracityLabel.MISLEADING,
            confidence=0.70,
            verdict_distribution={
                "MISLEADING": 0.70,
                "SUPPORTED": 0.12,
                "CONTRADICTED": 0.12,
                "OUTDATED": 0.03,
                "INSUFFICIENT_EVIDENCE": 0.03,
            },
            dimension_scores={
                "support_score": features.stance_support_score,
                "refute_score": features.stance_refute_score,
            },
            fusion_rationale=rationale,
        )


decision_matrix = MultimodalDecisionMatrix()
