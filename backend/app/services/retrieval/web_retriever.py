from datetime import datetime, timezone
import hashlib
from urllib.parse import urlparse
import httpx
from backend.app.core.config import settings
from backend.app.schemas.evidence import EvidenceSnippet
from backend.app.schemas.veracity import StanceType
from backend.app.services.retrieval.factcheck_cache import factcheck_cache_service

# Domain reputation multipliers based on journalistic verification standards
AUTHORITATIVE_DOMAINS = {
    "reuters.com": 1.6,
    "apnews.com": 1.6,
    "bbc.com": 1.5,
    "bbc.co.uk": 1.5,
    "snopes.com": 1.6,
    "politifact.com": 1.6,
    "factcheck.org": 1.6,
    "who.int": 1.7,
    "cdc.gov": 1.7,
    "nasa.gov": 1.7,
    "nature.com": 1.8,
    "thehindu.com": 1.4,
    "indianexpress.com": 1.4,
}


class WebEvidenceRetriever:
    """Retrieves relevant evidence from ClaimReview caches and public web fact-checking resources."""

    def get_domain_weight(self, domain: str) -> float:
        clean = domain.lower().replace("www.", "")
        if clean in AUTHORITATIVE_DOMAINS:
            return AUTHORITATIVE_DOMAINS[clean]
        if clean.endswith(".gov") or clean.endswith(".edu"):
            return 1.6
        return 1.0

    async def retrieve_evidence(self, claim_id: str, claim_text: str, search_queries: list[str]) -> list[EvidenceSnippet]:
        evidence_list: list[EvidenceSnippet] = []

        # 1. Fast local ClaimReview lookup
        local_matches = factcheck_cache_service.search_local_cache(claim_text, threshold=0.25)
        for item in local_matches:
            item.claim_id = claim_id
            evidence_list.append(item)

        # 2. Live Google Fact Check Tools API query (if API key configured)
        if settings.GOOGLE_FACTCHECK_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    api_url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
                    params = {
                        "query": claim_text,
                        "key": settings.GOOGLE_FACTCHECK_API_KEY,
                        "pageSize": 3
                    }
                    resp = await client.get(api_url, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        for claim_item in data.get("claims", []):
                            reviews = claim_item.get("claimReview", [])
                            for rev in reviews:
                                pub = rev.get("publisher", {}).get("name", "Fact-Checker")
                                url = rev.get("url", "")
                                domain = urlparse(url).netloc
                                rating = rev.get("textualRating", "")
                                snippet_text = f"Fact-check by {pub} on '{claim_item.get('text', '')}': Rated '{rating}'."
                                
                                is_false = any(w in rating.lower() for w in ["false", "pants on fire", "incorrect", "misleading"])
                                stance = StanceType.REFUTES if is_false else StanceType.SUPPORTS

                                evidence_list.append(EvidenceSnippet(
                                    id=f"gfc-{hashlib.md5(url.encode()).hexdigest()[:8]}",
                                    claim_id=claim_id,
                                    source_name=pub,
                                    source_url=url,
                                    domain=domain,
                                    domain_credibility_weight=self.get_domain_weight(domain),
                                    snippet_text=snippet_text,
                                    retrieval_score=0.85,
                                    stance=stance,
                                    stance_probabilities={
                                        "SUPPORTS": 0.05 if is_false else 0.90,
                                        "REFUTES": 0.90 if is_false else 0.05,
                                        "NEUTRAL": 0.05
                                    },
                                    is_claim_review=True,
                                    claim_review_rating=rating
                                ))
            except Exception:
                # Silently fall back to cached evidence on network/API failure
                pass

        # Deduplicate evidence by source_url
        seen_urls = set()
        deduped = []
        for ev in evidence_list:
            if ev.source_url not in seen_urls:
                seen_urls.add(ev.source_url)
                deduped.append(ev)

        return deduped


web_retriever = WebEvidenceRetriever()
