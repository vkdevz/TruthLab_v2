from backend.app.schemas.fusion import FusionFeatureVector, FusionDecision
from backend.app.schemas.claim import AtomicClaim
from backend.app.schemas.evidence import EvidenceSnippet
from backend.app.schemas.media import ImageForensicIndicators, VideoForensicIndicators
from backend.app.schemas.temporal import TemporalVerificationResult
from backend.app.ml.fusion.cross_modal_alignment import cross_modal_alignment
from backend.app.ml.fusion.decision_matrix import decision_matrix


class MultimodalFusionModel:
    """End-to-end multimodal evidence fusion service."""

    def fuse(
        self,
        claim: AtomicClaim,
        evidence_items: list[EvidenceSnippet],
        temporal_res: TemporalVerificationResult | None = None,
        image_forensics: ImageForensicIndicators | None = None,
        video_forensics: VideoForensicIndicators | None = None,
        ocr_text: str | None = None,
        temporal_result: TemporalVerificationResult | None = None,
    ) -> FusionDecision:
        t_res = temporal_res or temporal_result

        # 1. Compute Stance aggregations
        total_support = 0.0
        total_refute = 0.0
        sufficiency = 0.0

        for ev in evidence_items:
            domain_weight = ev.domain_credibility_weight
            if ev.is_claim_review and domain_weight <= 1.0:
                domain_weight = 1.5
            weight = ev.retrieval_score * domain_weight
            sufficiency += weight
            p_sup = ev.stance_probabilities.get("SUPPORTS", 0.0)
            p_ref = ev.stance_probabilities.get("REFUTES", 0.0)
            total_support += weight * p_sup
            total_refute += weight * p_ref

        denom = total_support + total_refute + 1e-6
        stance_sup = total_support / denom if sufficiency > 0 else 0.0
        stance_ref = total_refute / denom if sufficiency > 0 else 0.0

        # 2. Temporal penalty
        temporal_penalty = 0.0
        if t_res:
            if t_res.is_outdated or t_res.temporal_status == "OUTDATED":
                temporal_penalty = 0.95
            elif t_res.is_anachronistic:
                temporal_penalty = 0.70

        # 3. Media manipulation score
        manip_score = 0.0
        if image_forensics:
            manip_score = max(
                image_forensics.synthetic_probability,
                0.85 if image_forensics.is_ela_spliced else 0.0
            )
        elif video_forensics and video_forensics.synthetic_face_probability:
            manip_score = video_forensics.synthetic_face_probability

        # 4. Cross-modal alignment
        alignment_score, alignment_notes = cross_modal_alignment.compute_alignment(
            claim_text=claim.canonical_claim,
            ocr_text=ocr_text,
            image_forensics=image_forensics,
            video_forensics=video_forensics,
        )

        features = FusionFeatureVector(
            stance_refute_score=round(float(stance_ref), 3),
            stance_support_score=round(float(stance_sup), 3),
            temporal_penalty=round(float(temporal_penalty), 3),
            media_manipulation_score=round(float(manip_score), 3),
            evidence_sufficiency=round(float(sufficiency), 3),
            cross_modal_alignment=round(float(alignment_score), 3),
        )

        all_notes = alignment_notes + (temporal_res.temporal_notes if temporal_res else [])
        decision = decision_matrix.resolve(features, notes=all_notes)
        return decision


multimodal_fusion_model = MultimodalFusionModel()
