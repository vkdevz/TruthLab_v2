from abc import ABC, abstractmethod
import math
from sklearn.feature_extraction.text import TfidfVectorizer
from backend.app.schemas.evidence import EvidenceSnippet


class BaseEvidenceRanker(ABC):
    @abstractmethod
    def rank_evidence(self, claim_text: str, candidate_evidence: list[EvidenceSnippet], top_k: int = 5) -> list[EvidenceSnippet]:
        pass


class HybridEvidenceRanker(BaseEvidenceRanker):
    """Hybrid ranker combining lexical overlap, TF-IDF cosine similarity,
    source credibility multipliers, and ClaimReview provenance."""

    def rank_evidence(self, claim_text: str, candidate_evidence: list[EvidenceSnippet], top_k: int = 5) -> list[EvidenceSnippet]:
        if not candidate_evidence:
            return []

        docs = [claim_text] + [item.snippet_text for item in candidate_evidence]

        try:
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
            tfidf_matrix = vectorizer.fit_transform(docs)
            claim_vec = tfidf_matrix[0]

            for i, item in enumerate(candidate_evidence):
                snippet_vec = tfidf_matrix[i + 1]
                dot = (claim_vec * snippet_vec.T).toarray()[0][0]
                norm_c = math.sqrt((claim_vec * claim_vec.T).toarray()[0][0])
                norm_s = math.sqrt((snippet_vec * snippet_vec.T).toarray()[0][0])

                sim = dot / (norm_c * norm_s) if (norm_c * norm_s) > 0 else 0.05

                if item.is_claim_review:
                    # Verified ClaimReview matched by fact-check index: retain its authoritative score
                    sim = max(item.retrieval_score, sim * 1.35)
                else:
                    if sim >= 0.10:
                        sim = min(1.0, max(sim, item.retrieval_score * 0.85))
                    else:
                        sim = min(sim, 0.05)

                item.retrieval_score = round(max(0.01, min(1.0, float(sim))), 3)

        except Exception:
            # Fallback to existing retrieval scores if vectorization fails
            pass

        # Sort descending by effective score: retrieval_score * domain_credibility_weight
        candidate_evidence.sort(
            key=lambda x: x.retrieval_score * x.domain_credibility_weight,
            reverse=True
        )

        return candidate_evidence[:top_k]


hybrid_evidence_ranker = HybridEvidenceRanker()
