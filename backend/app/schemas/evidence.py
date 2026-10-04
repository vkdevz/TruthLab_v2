from datetime import datetime
from pydantic import BaseModel, Field
from .veracity import StanceType


class EvidenceSnippet(BaseModel):
    id: str = Field(..., description="Unique evidence snippet ID")
    claim_id: str = Field(..., description="Foreign key linking to target AtomicClaim")
    source_name: str = Field(..., description="Publisher or repository name (e.g. PolitiFact, Reuters, Snopes)")
    source_url: str = Field(..., description="Direct citation URL")
    domain: str = Field(..., description="Base domain (e.g., politifact.com)")
    domain_credibility_weight: float = Field(default=1.0, ge=0.1, le=2.0, description="Reputation multiplier")
    snippet_text: str = Field(..., description="Extracted relevant text excerpt")
    publication_date: datetime | None = Field(default=None, description="Reported publication timestamp")
    retrieval_score: float = Field(..., ge=0.0, le=1.0, description="Cross-encoder semantic similarity/relevance")
    stance: StanceType = Field(default=StanceType.NEUTRAL, description="NLI stance: SUPPORTS, REFUTES, NEUTRAL")
    stance_probabilities: dict[str, float] = Field(
        default_factory=lambda: {"SUPPORTS": 0.0, "REFUTES": 0.0, "NEUTRAL": 1.0},
        description="Softmax probability distribution over stance types"
    )
    is_claim_review: bool = Field(default=False, description="Whether this source is an official ClaimReview fact-check")
    claim_review_rating: str | None = Field(default=None, description="Original rating if ClaimReview (e.g. 'False')")
