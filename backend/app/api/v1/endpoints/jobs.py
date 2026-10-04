from fastapi import APIRouter, HTTPException
from backend.app.services.job_manager import job_manager

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/{job_id}")
async def get_job_status(job_id: str):
    status = await job_manager.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return status
