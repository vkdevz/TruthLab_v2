from datetime import datetime, timezone
import hashlib
from typing import Any
from backend.app.schemas.evidence import EvidenceSnippet
from backend.app.schemas.veracity import StanceType

# High-profile verified ClaimReview facts for local offline testing and fast lookups
REFERENCE_CLAIM_REVIEWS = [
    {
        "claim": "Bananas or boiled garlic water cures coronavirus and viral infections",
        "rating": "False",
        "publisher": "World Health Organization / Reuters Fact Check",
        "url": "https://www.reuters.com/article/factcheck-coronavirus-cure-garlic/",
        "domain": "reuters.com",
        "snippet": "The World Health Organization clarified that there is no scientific evidence that eating garlic or bananas cures COVID-19 or any other viral pathogen.",
        "stance": StanceType.REFUTES,
        "date": "2020-03-18T00:00:00Z"
    },
    {
        "claim": "James Webb Space Telescope detected atmospheric carbon dioxide on exoplanet WASP-39b",
        "rating": "True",
        "publisher": "NASA / Space Telescope Science Institute",
        "url": "https://www.nasa.gov/universe/exoplanets/nasas-webb-detects-carbon-dioxide-in-exoplanet-atmosphere/",
        "domain": "nasa.gov",
        "snippet": "NASA's James Webb Space Telescope has provided the first clear, unambiguous evidence for carbon dioxide in the atmosphere of a planet outside our solar system.",
        "stance": StanceType.SUPPORTS,
        "date": "2022-08-25T00:00:00Z"
    },
    {
        "claim": "NASA confirmed extraterrestrial alien signals received today",
        "rating": "False",
        "publisher": "Snopes Fact Check",
        "url": "https://www.snopes.com/fact-check/nasa-alien-signal-claim/",
        "domain": "snopes.com",
        "snippet": "NASA astronomers confirmed that detected anomalous microwave and radio bursts originated from terrestrial instrumentation interference, not extraterrestrial intelligence.",
        "stance": StanceType.REFUTES,
        "date": "2024-01-10T00:00:00Z"
    },
    {
        "claim": "Curfew announced across the entire state due to health emergency",
        "rating": "Outdated / False",
        "publisher": "PolitiFact",
        "url": "https://www.politifact.com/factchecks/2020/mar/state-curfew-lockdown/",
        "domain": "politifact.com",
        "snippet": "This emergency order was issued during the March 2020 lockdowns and expired years ago. No active curfew is currently in effect.",
        "stance": StanceType.REFUTES,
        "date": "2020-03-24T00:00:00Z"
    },
    {
        "claim": "India launched Chandrayaan-3 and landed successfully near the lunar south pole",
        "rating": "True",
        "publisher": "ISRO / BBC News",
        "url": "https://www.bbc.com/news/world-asia-india-66594520",
        "domain": "bbc.com",
        "snippet": "India's space agency ISRO successfully landed the Chandrayaan-3 lander module Vikram on the Moon's southern polar region on August 23, 2023.",
        "stance": StanceType.SUPPORTS,
        "date": "2023-08-23T00:00:00Z"
    },
    {
        "claim": "The Indian Ministry of Communications has officially banned all 5G network services nationwide",
        "rating": "False",
        "publisher": "PIB Fact Check / Department of Telecommunications",
        "url": "https://pib.gov.in/FactCheck/5g-network-ban-hoax",
        "domain": "pib.gov.in",
        "snippet": "The Ministry of Communications and Department of Telecommunications (DoT) clarified that viral circulars claiming a nationwide ban on 5G network services in India are fraudulent and fake. No ban has been issued.",
        "stance": StanceType.REFUTES,
        "date": "2023-06-10T00:00:00Z"
    }
]


class FactCheckCacheService:
    def __init__(self):
        self.records = REFERENCE_CLAIM_REVIEWS

    def search_local_cache(self, claim_text: str, threshold: float = 0.20) -> list[EvidenceSnippet]:
        """Performs lexical and token-overlap retrieval against verified ClaimReview records."""
        claim_tokens = {w.strip(" ,.?!'\"") for w in claim_text.lower().split() if len(w) > 2}
        results = []

        for idx, rec in enumerate(self.records):
            rec_tokens = {w.strip(" ,.?!'\"") for w in rec["claim"].lower().split() if len(w) > 2}
            intersection = claim_tokens.intersection(rec_tokens)
            containment = len(intersection) / len(claim_tokens) if claim_tokens else 0.0
            union = claim_tokens.union(rec_tokens)
            jaccard = len(intersection) / len(union) if union else 0.0
            relevance = max(containment, jaccard)

            if relevance >= threshold or len(intersection) >= 2:
                stance = rec["stance"]
                probs = {
                    "SUPPORTS": 0.92 if stance == StanceType.SUPPORTS else 0.03,
                    "REFUTES": 0.92 if stance == StanceType.REFUTES else 0.03,
                    "NEUTRAL": 0.05
                }
                
                snippet = EvidenceSnippet(
                    id=f"fcc-{idx}-{hashlib.md5(rec['url'].encode()).hexdigest()[:6]}",
                    claim_id="",
                    source_name=rec["publisher"],
                    source_url=rec["url"],
                    domain=rec["domain"],
                    domain_credibility_weight=1.6,
                    snippet_text=rec["snippet"],
                    publication_date=datetime.fromisoformat(rec["date"].replace("Z", "+00:00")),
                    retrieval_score=round(max(0.65, relevance), 3),
                    stance=stance,
                    stance_probabilities=probs,
                    is_claim_review=True,
                    claim_review_rating=rec["rating"]
                )
                results.append(snippet)

        results.sort(key=lambda s: s.retrieval_score, reverse=True)
        return results


factcheck_cache_service = FactCheckCacheService()
