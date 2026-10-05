import pytest
from io import BytesIO
from pathlib import Path
from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient

from backend.app.ingestion.url_ingest import URLValidator
from backend.app.services.storage import StorageService
from backend.app.main import app


client = TestClient(app)


class TestSSRFProtections:
    """Rigorous evaluation of Anti-SSRF defensive mechanisms."""

    @pytest.mark.parametrize("invalid_url", [
        "http://127.0.0.1/admin",
        "http://localhost:8000/api",
        "http://0.0.0.0/debug",
        "http://10.0.0.5/secrets",
        "http://192.168.1.1/router",
        "http://172.16.0.1/internal",
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://100.64.0.1/cgnat",
        "http://[::1]/ipv6_loopback",
        "ftp://ftp.example.com/file",
        "file:///etc/passwd",
        "gopher://gopher.example.com/path",
        "http://admin:secret@example.com",
        "http://example.com\x00extra",
        "http://example.com:22/ssh",
        "http://example.com:6379/redis",
        "http://example.com:9200/elastic",
    ])
    def test_ssrf_forbidden_targets(self, invalid_url: str):
        with pytest.raises(HTTPException) as exc_info:
            URLValidator.validate_url(invalid_url)
        assert exc_info.value.status_code == 400


class TestUploadSecurity:
    """Security verification for uploads, directory traversal, and magic bytes."""

    def test_filename_sanitization_path_traversal(self, tmp_path: Path):
        storage = StorageService(upload_dir=tmp_path)
        
        # Test directory traversal patterns
        clean_1 = storage.sanitize_filename("../../../etc/passwd.jpg")
        assert "/" not in clean_1
        assert ".." not in clean_1
        assert clean_1 == "passwd.jpg"

        clean_2 = storage.sanitize_filename("..\\..\\windows\\system32.png")
        assert "\\" not in clean_2
        assert ".." not in clean_2

        # Null byte removal
        clean_3 = storage.sanitize_filename("photo\x00.png")
        assert "\x00" not in clean_3

        # Hidden file prefix handling
        clean_4 = storage.sanitize_filename(".hidden_script.jpg")
        assert not clean_4.startswith(".")

    @pytest.mark.asyncio
    async def test_disguised_file_rejected_by_magic_bytes(self, tmp_path: Path):
        storage = StorageService(upload_dir=tmp_path)
        
        # Craft a file with .jpg extension but text content (no JPEG magic bytes)
        fake_content = b"#!/bin/bash\necho 'malicious script'"
        fake_upload = UploadFile(
            filename="innocent_image.jpg",
            file=BytesIO(fake_content),
            headers={"content-type": "image/jpeg"}
        )

        with pytest.raises(HTTPException) as exc_info:
            await storage.save_upload_file(fake_upload, is_video=False)
        assert exc_info.value.status_code == 400
        assert "file signature" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_genuine_jpeg_magic_bytes_accepted(self, tmp_path: Path):
        storage = StorageService(upload_dir=tmp_path)
        
        # Proper JPEG header bytes (\xFF\xD8\xFF)
        jpeg_header = b"\xFF\xD8\xFF\xE0\x00\x10JFIF" + b"\x00" * 100
        valid_upload = UploadFile(
            filename="real_photo.jpg",
            file=BytesIO(jpeg_header),
            headers={"content-type": "image/jpeg"}
        )

        saved_path = await storage.save_upload_file(valid_upload, is_video=False)
        try:
            assert saved_path.exists()
            assert saved_path.suffix == ".jpg"
        finally:
            storage.cleanup_file(saved_path)

    @pytest.mark.asyncio
    async def test_empty_file_rejected(self, tmp_path: Path):
        storage = StorageService(upload_dir=tmp_path)
        empty_upload = UploadFile(
            filename="empty.png",
            file=BytesIO(b""),
            headers={"content-type": "image/png"}
        )
        with pytest.raises(HTTPException) as exc_info:
            await storage.save_upload_file(empty_upload, is_video=False)
        assert exc_info.value.status_code == 400


class TestSecurityHeaders:
    """Verify HTTP response defense-in-depth headers."""

    def test_security_headers_present_on_root(self):
        resp = client.get("/")
        assert resp.status_code == 200
        headers = resp.headers
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("X-XSS-Protection") == "1; mode=block"
        assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_security_headers_present_on_health(self):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        headers = resp.headers
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
