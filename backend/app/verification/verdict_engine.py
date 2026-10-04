from backend.app.schemas.veracity import VeracityLabel, StanceType
from backend.app.schemas.evidence import EvidenceSnippet
from backend.app.schemas.claim import AtomicClaim
from backend.app.schemas.media import ImageForensicIndicators, VideoForensicIndicators
from backend.app.schemas.verification import ClaimVerificationResult, AuditTrail
from backend.app.ml.context.temporal_verifier import temporal_verifier
from backend.app.ml.fusion.fusion_model import multimodal_fusion_model
from backend.app.core.config import settings


class FiveClassVerdictEngine:
    """Deterministic five-class veracity verdict engine implementing documented category precedence,
    fusing textual evidence, temporal status, and media forensics."""

    def evaluate_veracity(
        self,
        claim: AtomicClaim,
        evidence_items: list[EvidenceSnippet],
        image_forensics: ImageForensicIndicators | None = None,
        video_forensics: VideoForensicIndicators | None = None,
        ocr_text: str | None = None,
    ) -> ClaimVerificationResult:
        # Step 1: Calculate Evidence Sufficiency Score
        # S(E) = sum(retrieval_score * domain_credibility_weight)
        sufficiency_score = 0.0
        for ev in evidence_items:
            weight = ev.retrieval_score * ev.domain_credibility_weight
            if ev.is_claim_review and ev.domain_credibility_weight <= 1.0:
                weight *= 1.5
            sufficiency_score += weight

        # Step 2: Temporal & Contextual Verification
        temporal_res = temporal_verifier.verify_context(claim, evidence_items)

        # Step 3: Multimodal Late-Fusion (if media forensics or OCR text are present)
        if image_forensics or video_forensics or ocr_text:
            decision = multimodal_fusion_model.fuse(
                claim=claim,
                evidence_items=evidence_items,
                temporal_res=temporal_res,
                image_forensics=image_forensics,
                video_forensics=video_forensics,
                ocr_text=ocr_text,
            )

            support_citations = [ev.source_url for ev in evidence_items if ev.stance == StanceType.SUPPORTS]
            refute_citations = [ev.source_url for ev in evidence_items if ev.stance == StanceType.REFUTES]

            media_notes = []
            if image_forensics:
                media_notes.extend(image_forensics.forensic_notes)
            if video_forensics and video_forensics.synthetic_face_probability:
                media_notes.append(
                    f"Video keyframe synthetic probability estimate: {video_forensics.synthetic_face_probability:.2f}"
                )

            summary = " • ".join(decision.fusion_rationale) if decision.fusion_rationale else (
                f"Claim '{claim.canonical_claim}' evaluated to {decision.final_verdict.value} via late multimodal fusion."
            )

            audit = AuditTrail(
                summary=summary,
                supporting_citations=list(dict.fromkeys(support_citations))[:3],
                refuting_citations=list(dict.fromkeys(refute_citations))[:3],
                temporal_notes=temporal_res.temporal_notes,
                media_authenticity_notes=media_notes,
                limitations=[
                    "Verification is grounded in indexed fact-checks and authoritative web reports available at query time.",
                    "Media forensic signals represent probabilistic heuristics and compression indicators, not definitive proof.",
                ],
            )

            return ClaimVerificationResult(
                claim=claim,
                veracity=decision.final_verdict,
                confidence=decision.confidence,
                evidence_sufficiency_score=round(sufficiency_score, 3),
                is_temporal_mismatch=temporal_res.is_outdated or temporal_res.is_anachronistic,
                evidence_items=evidence_items[:5],
                audit=audit,
            )

        # Step 4: Text-Only Verification (Standard Phase 1 Pipeline)
        # Evidence Sufficiency Gate
        if sufficiency_score < settings.EVIDENCE_SUFFICIENCY_THRESHOLD or not evidence_items:
            audit = AuditTrail(
                summary="Available evidence is inadequate to empirically verify or refute this claim.",
                supporting_citations=[],
                refuting_citations=[],
                temporal_notes=temporal_res.temporal_notes,
                media_authenticity_notes=[],
                limitations=[
                    "No corroborating or refuting reports found across authoritative fact-checking indices or indexed web sources.",
                    "System withholds binary truth judgment to avoid ungrounded speculation.",
                ],
            )
            return ClaimVerificationResult(
                claim=claim,
                veracity=VeracityLabel.INSUFFICIENT_EVIDENCE,
                confidence=0.45,
                evidence_sufficiency_score=round(sufficiency_score, 3),
                is_temporal_mismatch=temporal_res.is_outdated or temporal_res.is_anachronistic,
                evidence_items=evidence_items,
                audit=audit,
            )

        # Aggregate Stance Weights
        total_support = 0.0
        total_refute = 0.0
        support_citations = []
        refute_citations = []

        for ev in evidence_items:
            eff_weight = ev.retrieval_score * ev.domain_credibility_weight
            p_sup = ev.stance_probabilities.get("SUPPORTS", 0.0)
            p_ref = ev.stance_probabilities.get("REFUTES", 0.0)

            total_support += eff_weight * p_sup
            total_refute += eff_weight * p_ref

            if ev.stance == StanceType.SUPPORTS:
                support_citations.append(ev.source_url)
            elif ev.stance == StanceType.REFUTES:
                refute_citations.append(ev.source_url)

        total_weight = total_support + total_refute + 1e-6
        support_ratio = total_support / total_weight
        refute_ratio = total_refute / total_weight

        is_explicitly_outdated = any(
            "outdated" in (ev.claim_review_rating or "").lower()
            for ev in evidence_items
        )

        # Precedence Rule A: OUTDATED (Historical expired notice or recycled true event)
        if is_explicitly_outdated or (temporal_res.is_outdated and support_ratio >= 0.40):
            veracity = VeracityLabel.OUTDATED
            confidence = 0.90
            summary = (
                f"The claim '{claim.canonical_claim}' references a historical event or expired notice "
                f"({temporal_res.evidence_date.strftime('%Y-%m-%d') if temporal_res.evidence_date else 'in the past'}), "
                f"but is being recirculated out-of-context as current news."
            )

        # Precedence Rule B: CONTRADICTED (Authoritative evidence directly refutes the claim)
        elif refute_ratio >= 0.60:
            veracity = VeracityLabel.CONTRADICTED
            confidence = round(min(0.96, 0.65 + 0.30 * refute_ratio), 3)
            summary = (
                f"The claim '{claim.canonical_claim}' is directly contradicted by reliable evidence "
                f"from {len(refute_citations)} authoritative source(s)."
            )

        # Precedence Rule C: MISLEADING (Geographic mismatch, cherry-picking, or conflicting evidence)
        elif temporal_res.location_match_status == "MISMATCH":
            veracity = VeracityLabel.MISLEADING
            confidence = 0.82
            summary = f"The claim '{claim.canonical_claim}' is misleading due to geographic recontextualization."

        # Precedence Rule D: SUPPORTED (Sufficient corroboration, contemporaneous, authentic)
        elif support_ratio >= 0.65:
            veracity = VeracityLabel.SUPPORTED
            confidence = round(min(0.96, 0.65 + 0.30 * support_ratio), 3)
            summary = (
                f"The claim '{claim.canonical_claim}' is corroborated by reliable evidence "
                f"from {len(support_citations)} source(s)."
            )

        # Precedence Rule E: MISLEADING (Inconclusive / contradictory balance)
        else:
            veracity = VeracityLabel.MISLEADING
            confidence = 0.72
            summary = (
                f"The claim '{claim.canonical_claim}' presents conflicting or selective evidence: "
                f"supported by some reports while contested by others."
            )

        audit = AuditTrail(
            summary=summary,
            supporting_citations=list(dict.fromkeys(support_citations))[:3],
            refuting_citations=list(dict.fromkeys(refute_citations))[:3],
            temporal_notes=temporal_res.temporal_notes,
            media_authenticity_notes=[],
            limitations=[
                "Verification is grounded in indexed fact-checks and authoritative web reports available at query time.",
                "System distinguishes evidentiary support from unverified speculation.",
            ],
        )

        return ClaimVerificationResult(
            claim=claim,
            veracity=veracity,
            confidence=confidence,
            evidence_sufficiency_score=round(sufficiency_score, 3),
            is_temporal_mismatch=temporal_res.is_outdated or temporal_res.is_anachronistic,
            evidence_items=evidence_items[:5],
            audit=audit,
        )


verdict_engine = FiveClassVerdictEngine()

