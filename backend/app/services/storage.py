import os
import re
import shutil
import time
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from backend.app.core.config import settings

# Allowed extensions
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

# Allowed MIME types
ALLOWED_IMAGE_MIMES = {
    "image/jpeg", "image/jpg", "image/png", "image/webp", "image/bmp", "image/x-ms-bmp", "application/octet-stream"
}
ALLOWED_VIDEO_MIMES = {
    "video/mp4", "video/quicktime", "video/webm", "video/x-msvideo", "video/x-matroska", "application/octet-stream"
}

# Known file signatures (magic bytes)
IMAGE_MAGIC_SIGNATURES = [
    (b"\xFF\xD8\xFF", ".jpg"),           # JPEG
    (b"\x89PNG\r\n\x1a\n", ".png"),      # PNG
    (b"RIFF", ".webp"),                 # WEBP (starts with RIFF....WEBP)
    (b"BM", ".bmp"),                    # BMP
]

VIDEO_MAGIC_SIGNATURES = [
    (b"ftyp", ".mp4"),                  # MP4 / MOV (often offset by 4 bytes)
    (b"\x1A\x45\xDF\xA3", ".webm"),      # Matroska / WebM
    (b"RIFF", ".avi"),                  # AVI (RIFF....AVI )
    (b"moov", ".mov"),                  # QuickTime
    (b"wide", ".mov"),                  # QuickTime
]


class StorageService:
    """Safe media storage service implementing MIME validation, magic byte signature checks,
    path traversal prevention, and safe temporary file lifecycle management."""

    def __init__(self, upload_dir: Path | None = None):
        self.upload_dir = upload_dir or settings.UPLOADS_DIR
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def validate_magic_bytes(self, header: bytes, is_video: bool) -> bool:
        """Inspects file signature magic bytes to verify media authenticity."""
        if not header or len(header) < 4:
            return False

        if is_video:
            # Check for Matroska / WebM / AVI
            if header.startswith(b"\x1A\x45\xDF\xA3") or header.startswith(b"RIFF"):
                return True
            # MP4/MOV usually has 'ftyp', 'moov', 'mdat', or 'wide' in the first 16 bytes
            if b"ftyp" in header[:32] or b"moov" in header[:32] or b"mdat" in header[:32]:
                return True
            return False
        else:
            # JPEG
            if header.startswith(b"\xFF\xD8\xFF"):
                return True
            # PNG
            if header.startswith(b"\x89PNG\r\n\x1a\n"):
                return True
            # WEBP: RIFF + 4 bytes + WEBP
            if header.startswith(b"RIFF") and len(header) >= 12 and header[8:12] == b"WEBP":
                return True
            # BMP
            if header.startswith(b"BM"):
                return True
            return False

    def sanitize_filename(self, filename: str | None) -> str:
        """Prevents path traversal and removes control or invalid characters."""
        if not filename:
            return "unnamed_media"
        # Remove null bytes and control chars
        filename = filename.replace("\x00", "")
        # Take basename only to prevent directory traversal
        base = Path(filename).name
        # Scrub traversal tokens and directory separators
        base = base.replace("/", "").replace("\\", "").replace("..", "")
        # Allow only alphanumeric, dashes, underscores, and dots
        clean = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", base)
        if not clean or clean.startswith("."):
            clean = f"media_{clean}"
        return clean[:120]

    async def save_upload_file(self, upload_file: UploadFile, is_video: bool = False) -> Path:
        raw_filename = upload_file.filename or ""
        sanitized_name = self.sanitize_filename(raw_filename)
        original_ext = Path(sanitized_name).suffix.lower()

        allowed_exts = ALLOWED_VIDEO_EXTENSIONS if is_video else ALLOWED_IMAGE_EXTENSIONS
        if original_ext not in allowed_exts:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file extension '{original_ext}'. Allowed formats: {', '.join(sorted(allowed_exts))}"
            )

        # Validate MIME type if provided
        content_type = (upload_file.content_type or "").lower()
        allowed_mimes = ALLOWED_VIDEO_MIMES if is_video else ALLOWED_IMAGE_MIMES
        if content_type and content_type not in allowed_mimes:
            # If MIME is provided and clearly mismatched, reject
            if not content_type.startswith("image/" if not is_video else "video/"):
                raise HTTPException(
                    status_code=415,
                    detail=f"Invalid MIME type '{content_type}' for {'video' if is_video else 'image'} upload."
                )

        max_size = settings.MAX_VIDEO_SIZE_BYTES if is_video else settings.MAX_IMAGE_SIZE_BYTES
        unique_id = uuid.uuid4().hex
        destination = self.upload_dir / f"{unique_id}{original_ext}"

        total_bytes = 0
        chunk_size = 1024 * 1024  # 1MB chunk
        header_bytes = b""

        try:
            with open(destination, "wb") as f_out:
                while chunk := await upload_file.read(chunk_size):
                    if len(header_bytes) < 64:
                        needed = 64 - len(header_bytes)
                        header_bytes += chunk[:needed]

                    total_bytes += len(chunk)
                    if total_bytes > max_size:
                        f_out.close()
                        destination.unlink(missing_ok=True)
                        max_mb = max_size // (1024 * 1024)
                        raise HTTPException(
                            status_code=413,
                            detail=f"File exceeds maximum allowed size of {max_mb} MB."
                        )
                    f_out.write(chunk)

            # Check for empty file
            if total_bytes == 0:
                destination.unlink(missing_ok=True)
                raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes).")

            # Check magic bytes signature
            if not self.validate_magic_bytes(header_bytes, is_video=is_video):
                destination.unlink(missing_ok=True)
                media_label = "video" if is_video else "image"
                raise HTTPException(
                    status_code=400,
                    detail=f"Corrupted or invalid {media_label} file signature. File header did not match expected media format."
                )

            return destination

        except HTTPException:
            destination.unlink(missing_ok=True)
            raise
        except Exception as exc:
            destination.unlink(missing_ok=True)
            raise HTTPException(status_code=500, detail=f"Failed to safely process upload: {str(exc)}")

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
