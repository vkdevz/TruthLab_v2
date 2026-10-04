from backend.app.schemas.evidence import EvidenceSnippet


class EvidenceSufficiencyMetric:
    """Computes a multi-factor Evidence Sufficiency Index S(E) accounting for
    retrieval similarity, source domain diversity, and ClaimReview corroboration."""

    def compute_sufficiency(self, evidence_items: list[EvidenceSnippet]) -> tuple[float, bool, list[str]]:
        if not evidence_items:
            return 0.0, False, ["Zero evidence passages retrieved."]

        notes = []
        raw_weighted_sum = sum(
            ev.retrieval_score * ev.domain_credibility_weight
            for ev in evidence_items
        )

        # Source diversity bonus: distinct domains increase reliability
        unique_domains = {ev.domain for ev in evidence_items if ev.domain}
        diversity_factor = 1.0 + 0.15 * min(len(unique_domains) - 1, 3)

        # ClaimReview authoritative anchor boost
        has_claim_review = any(ev.is_claim_review for ev in evidence_items)
        if has_claim_review:
            diversity_factor *= 1.25
            notes.append("Authoritative ClaimReview fact-checking record verified.")

        sufficiency_index = float(round(raw_weighted_sum * diversity_factor, 3))
        is_sufficient = sufficiency_index >= 1.20

        if is_sufficient:
            notes.append(
                f"Evidence Sufficiency Index ({sufficiency_index:.2f}) exceeds operational confidence threshold."
            )
        else:
            notes.append(
                f"Evidence Sufficiency Index ({sufficiency_index:.2f}) is below threshold (1.20). "
                f"Statistical risk of epistemic uncertainty."
            )

        return sufficiency_index, is_sufficient, notes


evidence_sufficiency_metric = EvidenceSufficiencyMetric()
