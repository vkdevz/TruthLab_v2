from backend.app.schemas.evidence import EvidenceSnippet
from backend.app.evidence.ranking import hybrid_evidence_ranker, HybridEvidenceRanker


class EvidenceReranker:
    """Reranks retrieved evidence passages according to semantic relevance with the target claim.
    Delegates to canonical HybridEvidenceRanker to maintain a single source of truth."""

    def __init__(self, ranker: HybridEvidenceRanker | None = None):
        self._ranker = ranker or hybrid_evidence_ranker

    def rerank(self, claim_text: str, evidence_items: list[EvidenceSnippet]) -> list[EvidenceSnippet]:
        if not evidence_items:
            return []
        return self._ranker.rank_evidence(claim_text, evidence_items, top_k=len(evidence_items))


evidence_reranker = EvidenceReranker()
