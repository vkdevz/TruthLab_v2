from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from pydantic import BaseModel, HttpUrl
from backend.app.services.storage import storage_service
from backend.app.services.scraper import scraper_service
from backend.app.services.job_manager import job_manager
from backend.app.schemas.veracity import ModalityType

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


class TextIngestRequest(BaseModel):
    text: str


class URLIngestRequest(BaseModel):
    url: str


async def process_dummy_job(job_id: str):
    """Stub processor for Phase 2 validating asynchronous lifecycle; replaced in subsequent ML phases."""
    await job_manager.update_progress(job_id, "PREPROCESSING", 25)
    await job_manager.update_progress(job_id, "ANALYZING", 75)
    await job_manager.complete_job(job_id, {
        "status": "INGESTED",
        "detail": "Ingestion successful. Verification pipeline ready."
    })


@router.post("/text")
async def ingest_text(payload: TextIngestRequest, background_tasks: BackgroundTasks):
    cleaned = payload.text.strip()
    if not cleaned or len(cleaned) < 5:
        raise HTTPException(status_code=400, detail="Text payload must contain at least 5 characters.")

    job_id = await job_manager.create_job(
        input_modality=ModalityType.TEXT.value,
        input_summary=cleaned[:200]
    )
    background_tasks.add_task(process_dummy_job, job_id)
    return {
        "job_id": job_id,
        "modality": ModalityType.TEXT.value,
        "status": "PENDING",
        "message": "Text queued for verification."
    }


@router.post("/url")
async def ingest_url(payload: URLIngestRequest, background_tasks: BackgroundTasks):
    article_data = await scraper_service.fetch_article_content(payload.url)
    
    summary = f"{article_data['title']} ({article_data['source_domain']})"
    job_id = await job_manager.create_job(
        input_modality=ModalityType.URL.value,
        input_summary=summary
    )
    background_tasks.add_task(process_dummy_job, job_id)
    return {
        "job_id": job_id,
        "modality": ModalityType.URL.value,
        "article": {
            "title": article_data["title"],
            "domain": article_data["source_domain"],
            "date": article_data["publication_date"],
            "length_chars": len(article_data["text"])
        },
        "status": "PENDING"
    }


@router.post("/media")
async def ingest_media(
    file: UploadFile = File(...),
    is_video: bool = Form(False),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    saved_path = await storage_service.save_upload_file(file, is_video=is_video)
    modality = ModalityType.VIDEO.value if is_video else ModalityType.IMAGE.value
    
    job_id = await job_manager.create_job(
        input_modality=modality,
        input_summary=f"File: {file.filename} ({saved_path.name})"
    )
    background_tasks.add_task(process_dummy_job, job_id)
    return {
        "job_id": job_id,
        "modality": modality,
        "filename": file.filename,
        "saved_path": str(saved_path),
        "status": "PENDING"
    }
