from pydantic import BaseModel, Field
from backend.app.schemas.veracity import VeracityLabel


class FusionFeatureVector(BaseModel):
    stance_refute_score: float = Field(..., ge=0.0, le=1.0)
    stance_support_score: float = Field(..., ge=0.0, le=1.0)
    temporal_penalty: float = Field(default=0.0, ge=0.0, le=1.0)
    media_manipulation_score: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_sufficiency: float = Field(..., ge=0.0)
    cross_modal_alignment: float = Field(default=1.0, ge=0.0, le=1.0)


class FusionDecision(BaseModel):
    final_verdict: VeracityLabel
    confidence: float = Field(..., ge=0.0, le=1.0)
    verdict_distribution: dict[str, float] = Field(
        default_factory=dict,
        description="Probability distribution across the 5 veracity classes"
    )
    dimension_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Component breakdown across evidentiary, temporal, and media axes"
    )
    fusion_rationale: list[str] = Field(default_factory=list)
