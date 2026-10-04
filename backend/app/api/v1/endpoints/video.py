from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.app.services.storage import storage_service
from backend.app.ml.video.video_pipeline import video_pipeline
from backend.app.schemas.video_analysis import VideoAnalysisResponse

router = APIRouter(prefix="/video", tags=["Video Intelligence"])


@router.post("/analyze", response_model=VideoAnalysisResponse)
async def analyze_video(file: UploadFile = File(...)):
    # 1. Save uploaded video to sanitized storage
    saved_path = await storage_service.save_upload_file(file, is_video=True)

    try:
        # 2. Execute end-to-end video pipeline
        response = await video_pipeline.process_video(
            video_path=saved_path,
            original_filename=file.filename or saved_path.name
        )
        return response

    finally:
        storage_service.cleanup_file(saved_path)
