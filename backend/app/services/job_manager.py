from datetime import datetime, timezone
import uuid
from typing import Any, Callable
from sqlalchemy import select, update
from backend.app.db.session import AsyncSessionLocal
from backend.app.db.models import VerificationJobRecord


class JobManager:
    async def create_job(self, input_modality: str, input_summary: str | None = None) -> str:
        job_id = str(uuid.uuid4())
        async with AsyncSessionLocal() as session:
            job = VerificationJobRecord(
                id=job_id,
                input_modality=input_modality,
                raw_input_summary=input_summary,
                status="PENDING",
                progress_percent=0,
                current_stage="INITIALIZING",
            )
            session.add(job)
            await session.commit()
        return job_id

    async def update_progress(self, job_id: str, stage: str, percent: int) -> None:
        async with AsyncSessionLocal() as session:
            stmt = (
                update(VerificationJobRecord)
                .where(VerificationJobRecord.id == job_id)
                .values(
                    status="PROCESSING",
                    current_stage=stage,
                    progress_percent=min(percent, 99),
                    updated_at=datetime.now(timezone.utc),
                )
            )
            await session.execute(stmt)
            await session.commit()

    async def complete_job(self, job_id: str, result_payload: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc)
        async with AsyncSessionLocal() as session:
            stmt = (
                update(VerificationJobRecord)
                .where(VerificationJobRecord.id == job_id)
                .values(
                    status="COMPLETED",
                    current_stage="FINISHED",
                    progress_percent=100,
                    result_payload=result_payload,
                    completed_at=now,
                    updated_at=now,
                )
            )
            await session.execute(stmt)
            await session.commit()

    async def fail_job(self, job_id: str, error_message: str) -> None:
        now = datetime.now(timezone.utc)
        async with AsyncSessionLocal() as session:
            stmt = (
                update(VerificationJobRecord)
                .where(VerificationJobRecord.id == job_id)
                .values(
                    status="FAILED",
                    current_stage="ERROR",
                    error_message=error_message,
                    updated_at=now,
                )
            )
            await session.execute(stmt)
            await session.commit()

    async def get_job_status(self, job_id: str) -> dict[str, Any] | None:
        async with AsyncSessionLocal() as session:
            stmt = select(VerificationJobRecord).where(VerificationJobRecord.id == job_id)
            result = await session.execute(stmt)
            job = result.scalar_one_or_none()
            if not job:
                return None
            return {
                "job_id": job.id,
                "input_modality": job.input_modality,
                "status": job.status,
                "progress_percent": job.progress_percent,
                "current_stage": job.current_stage,
                "error_message": job.error_message,
                "result": job.result_payload,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            }


job_manager = JobManager()
