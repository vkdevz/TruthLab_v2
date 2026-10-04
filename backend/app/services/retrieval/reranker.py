import math
from sklearn.feature_extraction.text import TfidfVectorizer
from backend.app.schemas.evidence import EvidenceSnippet


class EvidenceReranker:
    """Reranks retrieved evidence passages according to semantic relevance with the target claim."""

    def rerank(self, claim_text: str, evidence_items: list[EvidenceSnippet]) -> list[EvidenceSnippet]:
        if not evidence_items:
            return []

        docs = [claim_text] + [item.snippet_text for item in evidence_items]
        
        try:
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
            tfidf_matrix = vectorizer.fit_transform(docs)
            claim_vec = tfidf_matrix[0]

            for i, item in enumerate(evidence_items):
                snippet_vec = tfidf_matrix[i + 1]
                # Cosine similarity
                dot = (claim_vec * snippet_vec.T).toarray()[0][0]
                norm_c = math.sqrt((claim_vec * claim_vec.T).toarray()[0][0])
                norm_s = math.sqrt((snippet_vec * snippet_vec.T).toarray()[0][0])
                
                sim = dot / (norm_c * norm_s) if (norm_c * norm_s) > 0 else 0.1
                
                # Boost and preserve match if official ClaimReview
                if item.is_claim_review:
                    sim = max(item.retrieval_score, sim * 1.5, 0.85)
                else:
                    sim = max(item.retrieval_score * 0.7, sim)
                
                item.retrieval_score = round(max(0.1, min(1.0, float(sim))), 3)

        except Exception:
            # Fallback to existing retrieval scores
            pass

        # Sort descending by retrieval score * domain weight
        evidence_items.sort(
            key=lambda x: x.retrieval_score * x.domain_credibility_weight,
            reverse=True
        )
        return evidence_items


evidence_reranker = EvidenceReranker()
