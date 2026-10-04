import os
import shutil
import time
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from backend.app.core.config import settings

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


class StorageService:
    def __init__(self, upload_dir: Path | None = None):
        self.upload_dir = upload_dir or settings.UPLOADS_DIR
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload_file(self, upload_file: UploadFile, is_video: bool = False) -> Path:
        original_ext = Path(upload_file.filename or "").suffix.lower()
        allowed = ALLOWED_VIDEO_EXTENSIONS if is_video else ALLOWED_IMAGE_EXTENSIONS
        
        if original_ext not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format '{original_ext}'. Allowed formats: {', '.join(allowed)}"
            )

        max_size = settings.MAX_VIDEO_SIZE_BYTES if is_video else settings.MAX_IMAGE_SIZE_BYTES
        
        unique_name = f"{uuid.uuid4().hex}{original_ext}"
        destination = self.upload_dir / unique_name

        total_bytes = 0
        chunk_size = 1024 * 1024  # 1MB chunk

        with open(destination, "wb") as f_out:
            while chunk := await upload_file.read(chunk_size):
                total_bytes += len(chunk)
                if total_bytes > max_size:
                    f_out.close()
                    destination.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds maximum allowed size of {max_size // (1024 * 1024)} MB."
                    )
                f_out.write(chunk)

        return destination

    def cleanup_file(self, file_path: Path | str) -> None:
        try:
            p = Path(file_path)
            if p.exists() and p.is_file():
                p.unlink()
        except Exception:
            pass

    def purge_old_uploads(self, max_age_seconds: int = 7200) -> int:
        """Removes uploaded files older than max_age_seconds (default 2 hours)."""
        now = time.time()
        purged = 0
        for entry in self.upload_dir.iterdir():
            if entry.is_file():
                try:
                    if now - entry.stat().st_mtime > max_age_seconds:
                        entry.unlink()
                        purged += 1
                except Exception:
                    pass
        return purged


storage_service = StorageService()
