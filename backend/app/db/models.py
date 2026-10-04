from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, DateTime, Float, Integer, Text, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.session import Base


def utc_now():
    return datetime.now(timezone.utc)


class VerificationJobRecord(Base):
    __tablename__ = "verification_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    input_modality = Column(String(20), nullable=False)
    raw_input_summary = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="PENDING")  # PENDING, PROCESSING, COMPLETED, FAILED
    progress_percent = Column(Integer, nullable=False, default=0)
    current_stage = Column(String(50), nullable=True)  # e.g., "INGESTING", "CLAIM_DECOMPOSITION", "EVIDENCE_RETRIEVAL"
    error_message = Column(Text, nullable=True)
    
    # Store complete verified JSON payload upon completion
    result_payload = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    claims = relationship("ClaimLogRecord", back_populates="job", cascade="all, delete-orphan")


class ClaimLogRecord(Base):
    __tablename__ = "claims_log"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("verification_jobs.id"), nullable=False, index=True)
    raw_text = Column(Text, nullable=False)
    canonical_claim = Column(Text, nullable=False)
    checkworthy_score = Column(Float, nullable=False, default=0.0)
    is_checkworthy = Column(Boolean, nullable=False, default=True)
    veracity_verdict = Column(String(30), nullable=True)
    confidence = Column(Float, nullable=True)
    temporal_anchor = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    job = relationship("VerificationJobRecord", back_populates="claims")


class EvidenceCacheRecord(Base):
    __tablename__ = "evidence_cache"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query_hash = Column(String(64), nullable=False, index=True)
    query_text = Column(Text, nullable=False)
    source_name = Column(String(100), nullable=False)
    source_url = Column(Text, nullable=False)
    domain = Column(String(100), nullable=False, index=True)
    snippet_text = Column(Text, nullable=False)
    retrieval_score = Column(Float, nullable=False, default=0.0)
    stance = Column(String(20), nullable=True)
    is_claim_review = Column(Boolean, default=False)
    cached_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
