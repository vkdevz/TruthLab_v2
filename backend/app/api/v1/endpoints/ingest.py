from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from pydantic import BaseModel
from backend.app.services.storage import storage_service
from backend.app.services.scraper import scraper_service
from backend.app.services.job_manager import job_manager
from backend.app.services.pipeline_service import pipeline_service
from backend.app.schemas.veracity import ModalityType

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


class TextIngestRequest(BaseModel):
    text: str


class URLIngestRequest(BaseModel):
    url: str


async def execute_text_verification_job(job_id: str, text: str):
    """Executes asynchronous text verification pipeline."""
    try:
        await pipeline_service.verify_text(text, job_id=job_id)
    except Exception as exc:
        await job_manager.fail_job(job_id, str(exc))


async def execute_url_verification_job(job_id: str, url: str, preloaded_article: dict | None = None):
    """Executes asynchronous URL verification pipeline."""
    try:
        await pipeline_service.verify_url(url, job_id=job_id, preloaded_article=preloaded_article)
    except Exception as exc:
        await job_manager.fail_job(job_id, str(exc))


async def execute_media_verification_job(job_id: str, saved_path, filename: str, is_video: bool):
    """Executes asynchronous media verification pipeline."""
    try:
        if is_video:
            await pipeline_service.verify_video_path(saved_path, filename=filename, job_id=job_id, cleanup=True)
        else:
            await pipeline_service.verify_image_path(saved_path, filename=filename, job_id=job_id, cleanup=True)
    except Exception as exc:
        await job_manager.fail_job(job_id, str(exc))


@router.post("/text")
async def ingest_text(payload: TextIngestRequest, background_tasks: BackgroundTasks):
    cleaned = payload.text.strip()
    if not cleaned or len(cleaned) < 5:
        raise HTTPException(status_code=400, detail="Text payload must contain at least 5 characters.")

    job_id = await job_manager.create_job(
        input_modality=ModalityType.TEXT.value,
        input_summary=cleaned[:200]
    )
    background_tasks.add_task(execute_text_verification_job, job_id, cleaned)
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
    background_tasks.add_task(execute_url_verification_job, job_id, payload.url, article_data)
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
    background_tasks: BackgroundTasks = None
):
    if background_tasks is None:
        background_tasks = BackgroundTasks()
    saved_path = await storage_service.save_upload_file(file, is_video=is_video)
    modality = ModalityType.VIDEO.value if is_video else ModalityType.IMAGE.value
    
    job_id = await job_manager.create_job(
        input_modality=modality,
        input_summary=f"File: {file.filename} ({saved_path.name})"
    )
    background_tasks.add_task(execute_media_verification_job, job_id, saved_path, file.filename or saved_path.name, is_video)
    return {
        "job_id": job_id,
        "modality": modality,
        "filename": file.filename,
        "file_id": saved_path.name,
        "status": "PENDING"
    }
