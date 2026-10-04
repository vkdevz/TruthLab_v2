import io
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import HTTPException
from backend.app.main import app
from backend.app.services.scraper import scraper_service
from backend.app.db.session import init_db


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_ssrf_protection():
    # Loopback / localhost blocking
    with pytest.raises(HTTPException) as exc_info:
        scraper_service.validate_url_safety("http://localhost:8080/secret")
    assert exc_info.value.status_code == 400

    with pytest.raises(HTTPException) as exc_info:
        scraper_service.validate_url_safety("http://127.0.0.1/admin")
    assert exc_info.value.status_code == 400

    # Non HTTP/HTTPS scheme
    with pytest.raises(HTTPException) as exc_info:
        scraper_service.validate_url_safety("ftp://example.com/file")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_text_ingest_and_job_lifecycle():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Ingest valid text
        ingest_res = await ac.post("/api/v1/ingest/text", json={
            "text": "The Ministry of Health announced a new nationwide vaccination campaign beginning next Monday."
        })
        assert ingest_res.status_code == 200
        data = ingest_res.json()
        assert "job_id" in data
        job_id = data["job_id"]

        # Poll job status
        poll_res = await ac.get(f"/api/v1/jobs/{job_id}")
        assert poll_res.status_code == 200
        job_data = poll_res.json()
        assert job_data["job_id"] == job_id
        assert job_data["status"] in {"PENDING", "PROCESSING", "COMPLETED"}


@pytest.mark.asyncio
async def test_text_ingest_short_payload_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/ingest/text", json={"text": "Hi"})
        assert res.status_code == 400


@pytest.mark.asyncio
async def test_image_upload_and_storage():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create a small fake PNG byte buffer
        dummy_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        files = {"file": ("test_sample.png", io.BytesIO(dummy_png), "image/png")}
        
        res = await ac.post("/api/v1/ingest/media", files=files, data={"is_video": False})
        assert res.status_code == 200
        data = res.json()
        assert data["modality"] == "IMAGE"
        assert "job_id" in data
