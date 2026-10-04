from datetime import datetime, timezone
import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.db.models import VerificationJobRecord, ClaimLogRecord, EvidenceCacheRecord
from backend.app.schemas.veracity import ModalityType, VeracityLabel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class VerificationRepository:
    """Async repository providing persistence operations for verification jobs, claims, and evidence."""

    @staticmethod
    async def create_job(
        session: AsyncSession,
        input_modality: ModalityType,
        raw_input_summary: str,
        job_id: Optional[str] = None
    ) -> VerificationJobRecord:
        record_id = job_id or str(uuid.uuid4())
        job = VerificationJobRecord(
            id=record_id,
            input_modality=input_modality.value if hasattr(input_modality, "value") else str(input_modality),
            raw_input_summary=raw_input_summary[:2000] if raw_input_summary else "",
            status="PROCESSING",
            progress_percent=10,
            current_stage="INITIALIZED",
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        return job

    @staticmethod
    async def update_job_stage(
        session: AsyncSession,
        job_id: str,
        stage: str,
        progress_percent: int
    ) -> Optional[VerificationJobRecord]:
        job = await session.get(VerificationJobRecord, job_id)
        if job:
            job.current_stage = stage
            job.progress_percent = progress_percent
            job.updated_at = utc_now()
            await session.commit()
            await session.refresh(job)
        return job

    @staticmethod
    async def complete_job(
        session: AsyncSession,
        job_id: str,
        result_payload: Dict[str, Any]
    ) -> Optional[VerificationJobRecord]:
        job = await session.get(VerificationJobRecord, job_id)
        if job:
            job.status = "COMPLETED"
            job.progress_percent = 100
            job.current_stage = "COMPLETED"
            job.result_payload = result_payload
            job.completed_at = utc_now()
            job.updated_at = utc_now()
            await session.commit()
            await session.refresh(job)
        return job

    @staticmethod
    async def fail_job(
        session: AsyncSession,
        job_id: str,
        error_message: str
    ) -> Optional[VerificationJobRecord]:
        job = await session.get(VerificationJobRecord, job_id)
        if job:
            job.status = "FAILED"
            job.current_stage = "FAILED"
            job.error_message = error_message
            job.updated_at = utc_now()
            await session.commit()
            await session.refresh(job)
        return job

    @staticmethod
    async def record_claims(
        session: AsyncSession,
        job_id: str,
        claims_data: List[Dict[str, Any]]
    ) -> List[ClaimLogRecord]:
        records = []
        for c in claims_data:
            rec = ClaimLogRecord(
                id=c.get("id") or str(uuid.uuid4()),
                job_id=job_id,
                raw_text=c.get("raw_text", ""),
                canonical_claim=c.get("canonical_claim", ""),
                checkworthy_score=c.get("checkworthy_score", 0.0),
                is_checkworthy=c.get("is_checkworthy", True),
                veracity_verdict=c.get("veracity_verdict"),
                confidence=c.get("confidence"),
                temporal_anchor=c.get("temporal_anchor"),
            )
            session.add(rec)
            records.append(rec)
        await session.commit()
        return records

    @staticmethod
    async def get_job_by_id(
        session: AsyncSession,
        job_id: str
    ) -> Optional[VerificationJobRecord]:
        stmt = select(VerificationJobRecord).where(VerificationJobRecord.id == job_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


verification_repo = VerificationRepository()
