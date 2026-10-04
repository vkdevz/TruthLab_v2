from backend.app.schemas.veracity import VeracityLabel, StanceType
from backend.app.schemas.evidence import EvidenceSnippet
from backend.app.schemas.claim import AtomicClaim
from backend.app.schemas.verification import ClaimVerificationResult, AuditTrail
from backend.app.core.config import settings


class VeracityScorer:
    """Aggregates stances, computes evidence sufficiency, and assigns calibrated veracity verdicts."""

    def score_claim(self, claim: AtomicClaim, evidence_items: list[EvidenceSnippet]) -> ClaimVerificationResult:
        # 1. Compute Evidence Sufficiency Score: S(E) = sum(retrieval_score * domain_weight)
        sufficiency_score = sum(
            ev.retrieval_score * ev.domain_credibility_weight
            for ev in evidence_items
        )

        # 2. Check if evidence is insufficient
        if sufficiency_score < settings.EVIDENCE_SUFFICIENCY_THRESHOLD or not evidence_items:
            audit = AuditTrail(
                summary="Insufficient authoritative evidence found to empirically verify or refute this claim.",
                supporting_citations=[],
                refuting_citations=[],
                limitations=["No corroborating reports located in indexed fact-checks or primary sources."]
            )
            return ClaimVerificationResult(
                claim=claim,
                veracity=VeracityLabel.INSUFFICIENT_EVIDENCE,
                confidence=0.40,
                evidence_sufficiency_score=round(sufficiency_score, 3),
                evidence_items=evidence_items,
                audit=audit,
            )

        # 3. Aggregate weighted stance scores
        total_support_weight = 0.0
        total_refute_weight = 0.0
        support_citations = []
        refute_citations = []

        for ev in evidence_items:
            weight = ev.retrieval_score * ev.domain_credibility_weight
            p_sup = ev.stance_probabilities.get("SUPPORTS", 0.0)
            p_ref = ev.stance_probabilities.get("REFUTES", 0.0)

            total_support_weight += weight * p_sup
            total_refute_weight += weight * p_ref

            if ev.stance == StanceType.SUPPORTS:
                support_citations.append(ev.source_url)
            elif ev.stance == StanceType.REFUTES:
                refute_citations.append(ev.source_url)

        total_weight = total_support_weight + total_refute_weight + 1e-6
        support_ratio = total_support_weight / total_weight
        refute_ratio = total_refute_weight / total_weight

        # 4. Map to Veracity Taxonomy
        if refute_ratio >= 0.60:
            veracity = VeracityLabel.CONTRADICTED
            confidence = round(min(0.96, 0.60 + 0.35 * refute_ratio), 3)
            summary = (
                f"The claim '{claim.canonical_claim}' is directly contradicted by reliable evidence "
                f"from {len(refute_citations)} authoritative source(s)."
            )
        elif support_ratio >= 0.65:
            veracity = VeracityLabel.SUPPORTED
            confidence = round(min(0.96, 0.60 + 0.35 * support_ratio), 3)
            summary = (
                f"The claim '{claim.canonical_claim}' is substantiated by authoritative evidence "
                f"from {len(support_citations)} source(s)."
            )
        else:
            veracity = VeracityLabel.MISLEADING
            confidence = 0.72
            summary = (
                f"The claim '{claim.canonical_claim}' presents conflicting or selective evidence: "
                f"partially supported by some sources while contested by others."
            )

        audit = AuditTrail(
            summary=summary,
            supporting_citations=list(dict.fromkeys(support_citations))[:3],
            refuting_citations=list(dict.fromkeys(refute_citations))[:3],
            limitations=["Analysis reflects sources indexed as of verification query time."]
        )

        return ClaimVerificationResult(
            claim=claim,
            veracity=veracity,
            confidence=confidence,
            evidence_sufficiency_score=round(sufficiency_score, 3),
            evidence_items=evidence_items[:5],
            audit=audit,
        )


veracity_scorer = VeracityScorer()
