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
        from backend.app.evidence.provider import composite_evidence_retriever
        queries = search_queries or [claim_text]
        return await composite_evidence_retriever.retrieve_candidate_evidence(
            claim_id=claim_id,
            canonical_claim=claim_text,
            search_queries=queries
        )


web_retriever = WebEvidenceRetriever()
