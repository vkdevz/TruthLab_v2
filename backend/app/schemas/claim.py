from datetime import datetime
from pydantic import BaseModel, Field


class AtomicClaim(BaseModel):
    id: str = Field(..., description="Unique claim identifier within the job")
    raw_text: str = Field(..., description="Original extracted sentence or fragment")
    canonical_claim: str = Field(..., description="Normalized, standalone factual proposition")
    checkworthy_score: float = Field(..., ge=0.0, le=1.0, description="Probability that the claim is an empirical check-worthy proposition")
    is_checkworthy: bool = Field(..., description="Flag whether checkworthy_score >= threshold")
    entities: list[str] = Field(default_factory=list, description="Extracted named entities (people, orgs, locations)")
    temporal_anchor: str | None = Field(default=None, description="Explicit or inferred date string associated with the claim")
    inferred_date: datetime | None = Field(default=None, description="Parsed ISO datetime if temporal anchor is present")
    search_queries: list[str] = Field(default_factory=list, description="Formulated queries for evidence retrieval")
