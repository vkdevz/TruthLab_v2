from datetime import datetime
from pydantic import BaseModel, Field
from .claim import AtomicClaim
from .evidence import EvidenceSnippet
from .media import ImageForensicIndicators, VideoForensicIndicators
from .veracity import ModalityType, VeracityLabel


class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # "claim", "evidence", "source", "forensic"
    status: str | None = None


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str  # "SUPPORTS", "REFUTES", "CITES", "EXTRACTED_FROM"
    weight: float = 1.0


class EvidenceGraph(BaseModel):
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


class AuditTrail(BaseModel):
    summary: str
    supporting_citations: list[str] = Field(default_factory=list)
    refuting_citations: list[str] = Field(default_factory=list)
    temporal_notes: list[str] = Field(default_factory=list)
    media_authenticity_notes: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class ClaimVerificationResult(BaseModel):
    claim: AtomicClaim
    veracity: VeracityLabel
    confidence: float = Field(..., ge=0.0, le=1.0, description="Calibrated confidence score")
    evidence_sufficiency_score: float = Field(..., ge=0.0)
    is_temporal_mismatch: bool = False
    evidence_items: list[EvidenceSnippet] = Field(default_factory=list)
    audit: AuditTrail


class FullVerificationResponse(BaseModel):
    job_id: str
    created_at: datetime
    completed_at: datetime | None = None
    input_modality: ModalityType
    overall_veracity: VeracityLabel
    overall_confidence: float = Field(..., ge=0.0, le=1.0)
    claims_verified: list[ClaimVerificationResult] = Field(default_factory=list)
    image_forensics: ImageForensicIndicators | None = None
    video_forensics: VideoForensicIndicators | None = None
    ocr_text: str | None = None
    transcript_text: str | None = None
    evidence_graph: EvidenceGraph
    executive_summary: str
    system_limitations: list[str] = Field(default_factory=list)

