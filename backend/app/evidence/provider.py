import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
import re
from urllib.parse import urlparse
import httpx
from lxml import html
from backend.app.schemas.evidence import EvidenceSnippet
from backend.app.schemas.veracity import StanceType
from backend.app.core.config import settings
from backend.app.services.retrieval.factcheck_cache import REFERENCE_CLAIM_REVIEWS

logger = logging.getLogger("TruthLab.EvidenceProvider")

STOP_WORDS = {
    "the", "a", "an", "is", "was", "are", "were", "in", "on", "at", "by", "for", "with",
    "about", "against", "between", "into", "through", "during", "before", "after", "above",
    "below", "to", "from", "up", "down", "out", "off", "over", "under", "again", "further",
    "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only",
    "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don",
    "should", "now", "and", "or", "but", "if", "because", "as", "until", "while", "of",
    "confirmed", "reported", "announced", "revealed", "stated", "claims", "says", "today",
    "breaking", "news", "official", "officially"
}

CONTRADICTION_KEYWORDS = {
    "false", "fake", "incorrect", "debunked", "no evidence", "refuted", "denied", "hoax",
    "misleading", "fabricated", "unfounded", "untrue", "contrary", "disputed", "inaccurate",
    "never happened", "contradicts", "misinformation", "disinformation", "conspiracy theory"
}

ENTAILMENT_KEYWORDS = {
    "confirmed", "verified", "true", "accurate", "official", "published", "agreed",
    "corroborates", "evidence shows", "substantiated", "proven", "announced", "authenticated"
}


class EvidenceProvider(ABC):
    """Abstract Base Class for external and local evidence sources."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the evidence provider."""
        pass

    @abstractmethod
    async def retrieve(self, query: str, claim_id: str, limit: int = 5) -> list[EvidenceSnippet]:
        """Retrieves candidate evidence snippets matching the query."""
        pass


class LocalClaimReviewProvider(EvidenceProvider):
    """Local offline provider querying verified ClaimReview datasets and benchmark records."""

    def __init__(self, records: list[dict] | None = None):
        self.records = records if records is not None else self._load_all_records()

    def _load_all_records(self) -> list[dict]:
        all_recs = list(REFERENCE_CLAIM_REVIEWS)
        seen_urls = {r["url"] for r in all_recs}

        # Load reference claim reviews file if present
        ref_files = [
            settings.DATA_DIR / "claim_reviews" / "reference_claim_reviews.json",
            Path("data/claim_reviews/reference_claim_reviews.json"),
        ]
        for ref_file in ref_files:
            if ref_file.exists():
                try:
                    data = json.loads(ref_file.read_text())
                    for item in data:
                        if item.get("url") not in seen_urls:
                            all_recs.append(item)
                            seen_urls.add(item.get("url"))
                except Exception:
                    pass

        return all_recs

    @property
    def provider_name(self) -> str:
        return "Local ClaimReview Index"

    async def retrieve(self, query: str, claim_id: str, limit: int = 5) -> list[EvidenceSnippet]:
        # Filter stop words and punctuation (preserve 2-character domain terms like '5g', 'ai')
        query_words = [w.strip(" ,.?!'\"") for w in query.lower().split() if len(w) >= 2]
        query_tokens = {w for w in query_words if w not in STOP_WORDS}
        results = []

        if not query_tokens:
            return []

        for idx, rec in enumerate(self.records):
            rec_words = [w.strip(" ,.?!'\"") for w in rec["claim"].lower().split() if len(w) >= 2]
            rec_tokens = {w for w in rec_words if w not in STOP_WORDS}
            if not rec_tokens:
                continue

            intersection = query_tokens.intersection(rec_tokens)
            containment = len(intersection) / len(query_tokens) if query_tokens else 0.0
            union = query_tokens.union(rec_tokens)
            jaccard = len(intersection) / len(union) if union else 0.0
            relevance = max(containment, jaccard)

            # Match if at least 2 tokens match with relevance >= 0.20, or 1 specific token with high relevance >= 0.35
            if (len(intersection) >= 2 and relevance >= 0.20) or (len(intersection) >= 1 and relevance >= 0.35):
                raw_stance = rec.get("stance", "NEUTRAL")
                if isinstance(raw_stance, str):
                    try:
                        stance = StanceType(raw_stance)
                    except ValueError:
                        stance = StanceType.NEUTRAL
                else:
                    stance = raw_stance

                probs = {
                    "SUPPORTS": 0.92 if stance == StanceType.SUPPORTS else 0.03,
                    "REFUTES": 0.92 if stance == StanceType.REFUTES else 0.03,
                    "NEUTRAL": 0.05
                }

                date_val = None
                date_str = rec.get("date")
                if date_str:
                    try:
                        date_val = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    except Exception:
                        pass

                snippet = EvidenceSnippet(
                    id=f"loc-{idx}-{hashlib.md5(rec['url'].encode()).hexdigest()[:6]}",
                    claim_id=claim_id,
                    source_name=rec["publisher"],
                    source_url=rec["url"],
                    domain=rec.get("domain") or urlparse(rec["url"]).netloc,
                    domain_credibility_weight=1.6,
                    snippet_text=rec["snippet"],
                    publication_date=date_val,
                    retrieval_score=round(max(0.85, relevance), 3),
                    stance=stance,
                    stance_probabilities=probs,
                    is_claim_review=True,
                    claim_review_rating=rec.get("rating"),
                    provider=self.provider_name
                )
                results.append(snippet)

        results.sort(key=lambda s: s.retrieval_score, reverse=True)
        return results[:limit]


class WikipediaEvidenceProvider(EvidenceProvider):
    """Live encyclopedic knowledge retrieval using the public Wikipedia Search & Summary APIs."""

    def __init__(self):
        self.headers = {
            "User-Agent": "TruthLab/1.0 (academic research verification; mailto:truthlab@university.edu)"
        }

    @property
    def provider_name(self) -> str:
        return "Wikipedia Knowledge API"

    async def retrieve(self, query: str, claim_id: str, limit: int = 4) -> list[EvidenceSnippet]:
        # Clean query: strip punctuation, table artifacts, quotes
        clean_q = re.sub(r"[\n\r|#]+", " ", query).strip()
        # Remove meta search tokens if appended
        clean_q = re.sub(r"\b(fact check|verified|debunked|hoax)\b", "", clean_q, flags=re.IGNORECASE).strip()
        if len(clean_q) < 4:
            return []

        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": clean_q,
            "format": "json",
            "srlimit": limit,
        }

        results = []
        try:
            async with httpx.AsyncClient(timeout=4.0, headers=self.headers) as client:
                resp = await client.get(search_url, params=params)
                if resp.status_code != 200:
                    return []

                data = resp.json()
                items = data.get("query", {}).get("search", [])

                c_tokens = {w for w in clean_q.lower().split() if w not in STOP_WORDS and len(w) > 2}

                for item in items:
                    title = item.get("title", "")
                    if not title:
                        continue

                    # Fallback snippet from search API
                    raw_snip = item.get("snippet", "")
                    clean_snip = re.sub(r"<[^>]+>", "", raw_snip).strip()

                    # Try fetching full encyclopedic lead paragraph from REST summary
                    page_key = title.replace(" ", "_")
                    sum_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{page_key}"
                    try:
                        sum_resp = await client.get(sum_url, timeout=2.5)
                        if sum_resp.status_code == 200:
                            lead_extract = sum_resp.json().get("extract", "")
                            if lead_extract and len(lead_extract) > len(clean_snip):
                                clean_snip = lead_extract
                    except Exception:
                        pass

                    if not clean_snip or len(clean_snip) < 15:
                        continue

                    # Guard against irrelevant search hits (e.g. random TV episode list matching a single word)
                    art_tokens = {w for w in f"{title} {clean_snip}".lower().split() if w not in STOP_WORDS and len(w) > 2}
                    overlap = c_tokens.intersection(art_tokens)
                    containment = len(overlap) / len(c_tokens) if c_tokens else 0.0

                    # Reject loose hits that don't share at least 2 content terms or >= 25% overlap
                    if len(overlap) < 2 and containment < 0.25:
                        continue

                    page_url = f"https://en.wikipedia.org/wiki/{page_key}"

                    # Stance heuristic
                    s_lower = clean_snip.lower()
                    refute_hits = sum(1 for k in CONTRADICTION_KEYWORDS if k in s_lower)
                    support_hits = sum(1 for k in ENTAILMENT_KEYWORDS if k in s_lower)

                    if refute_hits > support_hits and refute_hits >= 1:
                        stance = StanceType.REFUTES
                        probs = {"SUPPORTS": 0.05, "REFUTES": 0.90, "NEUTRAL": 0.05}
                    elif support_hits >= 1:
                        stance = StanceType.SUPPORTS
                        probs = {"SUPPORTS": 0.90, "REFUTES": 0.05, "NEUTRAL": 0.05}
                    else:
                        stance = StanceType.SUPPORTS
                        probs = {"SUPPORTS": 0.85, "REFUTES": 0.05, "NEUTRAL": 0.10}

                    computed_score = round(min(0.95, max(0.45, containment * 1.1)), 3)

                    snippet = EvidenceSnippet(
                        id=f"wiki-{hashlib.md5(page_url.encode()).hexdigest()[:8]}",
                        claim_id=claim_id,
                        source_name=f"Wikipedia: {title}",
                        source_url=page_url,
                        domain="wikipedia.org",
                        domain_credibility_weight=1.5,
                        snippet_text=clean_snip,
                        publication_date=datetime.now(timezone.utc),
                        retrieval_score=computed_score,
                        stance=stance,
                        stance_probabilities=probs,
                        is_claim_review=False,
                        claim_review_rating=None,
                        provider=self.provider_name
                    )
                    results.append(snippet)
        except Exception as exc:
            logger.debug(f"Wikipedia retrieval failed for query '{query}': {exc}")

        return results[:limit]


class PublicWebSearchProvider(EvidenceProvider):
    """Live web search querying fact-checking and news sources via public search gateway."""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    @property
    def provider_name(self) -> str:
        return "DuckDuckGo Web Search"

    async def retrieve(self, query: str, claim_id: str, limit: int = 3) -> list[EvidenceSnippet]:
        clean_q = re.sub(r"[\n\r|#]+", " ", query).strip()
        if len(clean_q) < 5:
            return []

        search_q = f"site:snopes.com OR site:reuters.com OR site:apnews.com OR site:politifact.com {clean_q}"
        if getattr(self, "_consecutive_failures", 0) >= 2:
            return []

        results = []

        try:
            async with httpx.AsyncClient(timeout=2.5, headers=self.headers, follow_redirects=True) as client:
                resp = await client.post("https://lite.duckduckgo.com/lite/", data={"q": search_q})
                if resp.status_code == 200 and resp.text:
                    self._consecutive_failures = 0
                    tree = html.fromstring(resp.text)
                    links = tree.xpath('//a[@class="result-link"]')
                    snippets = tree.xpath('//td[@class="result-snippet"]')

                    c_tokens = {w for w in clean_q.lower().split() if w not in STOP_WORDS and len(w) > 2}

                    for link_elem, snip_elem in zip(links[:limit], snippets[:limit]):
                        href = link_elem.get("href", "")
                        # Unpack redirect if needed
                        if "duckduckgo.com/l/?uddg=" in href:
                            from urllib.parse import parse_qs
                            parsed = parse_qs(urlparse(href).query)
                            if "uddg" in parsed:
                                href = parsed["uddg"][0]

                        domain = urlparse(href).netloc
                        snip_text = snip_elem.text_content().strip()

                        if not href or not snip_text or len(snip_text) < 15:
                            continue

                        snip_tokens = {w for w in snip_text.lower().split() if w not in STOP_WORDS and len(w) > 2}
                        overlap = c_tokens.intersection(snip_tokens)
                        containment = len(overlap) / len(c_tokens) if c_tokens else 0.0

                        if len(overlap) < 2 and containment < 0.25:
                            continue

                        s_lower = snip_text.lower()
                        refute_hits = sum(1 for k in CONTRADICTION_KEYWORDS if k in s_lower)
                        support_hits = sum(1 for k in ENTAILMENT_KEYWORDS if k in s_lower)

                        if refute_hits > support_hits and refute_hits >= 1:
                            stance = StanceType.REFUTES
                            probs = {"SUPPORTS": 0.05, "REFUTES": 0.90, "NEUTRAL": 0.05}
                        else:
                            stance = StanceType.SUPPORTS
                            probs = {"SUPPORTS": 0.85, "REFUTES": 0.05, "NEUTRAL": 0.10}

                        computed_score = round(min(0.95, max(0.45, containment * 1.1)), 3)

                        results.append(EvidenceSnippet(
                            id=f"ddg-{hashlib.md5(href.encode()).hexdigest()[:8]}",
                            claim_id=claim_id,
                            source_name=link_elem.text_content().strip() or f"Web Source ({domain})",
                            source_url=href,
                            domain=domain,
                            domain_credibility_weight=1.6 if any(d in domain for d in ["reuters", "snopes", "politifact", "apnews"]) else 1.2,
                            snippet_text=snip_text,
                            publication_date=datetime.now(timezone.utc),
                            retrieval_score=computed_score,
                            stance=stance,
                            stance_probabilities=probs,
                            is_claim_review="fact-check" in href.lower() or "politifact" in domain or "snopes" in domain,
                            claim_review_rating="Verified Reporting",
                            provider=self.provider_name
                        ))
        except Exception as exc:
            self._consecutive_failures = getattr(self, "_consecutive_failures", 0) + 1
            logger.debug(f"Web search retrieval failed for query '{query}': {exc}")

        return results[:limit]


class GoogleFactCheckProvider(EvidenceProvider):
    """Live provider querying the official Google Fact Check Tools API."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.GOOGLE_FACTCHECK_API_KEY

    @property
    def provider_name(self) -> str:
        return "Google Fact Check Tools API"

    async def retrieve(self, query: str, claim_id: str, limit: int = 5) -> list[EvidenceSnippet]:
        if not self.api_key:
            logger.info("[EVIDENCE_AUDIT] Google Fact Check API key not configured; skipping Google Fact Check Tools API.")
            return []

        results = []
        api_url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
        params = {"query": query, "key": self.api_key, "pageSize": limit}

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(api_url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("claims", []):
                        for rev in item.get("claimReview", []):
                            pub = rev.get("publisher", {}).get("name", "Verified Fact-Checker")
                            url = rev.get("url", "")
                            domain = urlparse(url).netloc
                            rating = rev.get("textualRating", "")
                            snippet_text = f"Fact-check by {pub} on '{item.get('text', '')}': Rated '{rating}'."

                            is_false = any(w in rating.lower() for w in ["false", "pants on fire", "incorrect", "misleading"])
                            stance = StanceType.REFUTES if is_false else StanceType.SUPPORTS

                            results.append(EvidenceSnippet(
                                id=f"gfc-{hashlib.md5(url.encode()).hexdigest()[:8]}",
                                claim_id=claim_id,
                                source_name=pub,
                                source_url=url,
                                domain=domain,
                                domain_credibility_weight=1.6,
                                snippet_text=snippet_text,
                                retrieval_score=0.88,
                                stance=stance,
                                stance_probabilities={
                                    "SUPPORTS": 0.05 if is_false else 0.90,
                                    "REFUTES": 0.90 if is_false else 0.05,
                                    "NEUTRAL": 0.05
                                },
                                is_claim_review=True,
                                claim_review_rating=rating,
                                provider=self.provider_name
                            ))
        except Exception as exc:
            logger.debug(f"Google Fact Check API query failed: {exc}")

        return results[:limit]


class CompositeEvidenceRetriever:
    """Orchestrates evidence collection across all active registered providers:
    Local ClaimReview -> Wikipedia Knowledge API -> Public Web Search -> Google Fact Check.
    """

    def __init__(self, providers: list[EvidenceProvider] | None = None):
        self.providers = providers or [
            LocalClaimReviewProvider(),
            WikipediaEvidenceProvider(),
            PublicWebSearchProvider(),
            GoogleFactCheckProvider(),
        ]

    def register_provider(self, provider: EvidenceProvider):
        self.providers.append(provider)

    async def retrieve_candidate_evidence(
        self,
        claim_id: str,
        canonical_claim: str,
        search_queries: list[str],
        per_query_limit: int = 4
    ) -> list[EvidenceSnippet]:
        all_candidates: list[EvidenceSnippet] = []

        logger.info(f"[EVIDENCE_AUDIT] Initiating retrieval for claim: '{canonical_claim}' with {len(search_queries)} queries.")

        tasks = []
        for provider in self.providers:
            for q in search_queries:
                tasks.append(provider.retrieve(query=q, claim_id=claim_id, limit=per_query_limit))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for res in results:
            if isinstance(res, list):
                all_candidates.extend(res)
            elif isinstance(res, Exception):
                logger.debug(f"[EVIDENCE_AUDIT] Provider query exception: {res}")

        # Deduplicate candidates by source URL
        seen_urls = set()
        deduped = []
        for ev in all_candidates:
            if ev.source_url not in seen_urls:
                seen_urls.add(ev.source_url)
                deduped.append(ev)

        logger.info(
            f"[EVIDENCE_AUDIT] Total raw candidates: {len(all_candidates)}, Deduplicated candidates: {len(deduped)}"
        )
        for ev in deduped:
            logger.info(
                f"[EVIDENCE_AUDIT] Candidate | Provider: '{ev.provider}' | URL: {ev.source_url} | "
                f"Score: {ev.retrieval_score} | Stance: {ev.stance.value} | Credibility: {ev.domain_credibility_weight}"
            )

        return deduped


composite_evidence_retriever = CompositeEvidenceRetriever()
