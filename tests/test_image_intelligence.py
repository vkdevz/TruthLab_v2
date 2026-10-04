import io
from pathlib import Path
from PIL import Image, PngImagePlugin
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.ml.image.ocr_engine import ocr_engine
from backend.app.ml.image.metadata_forensics import metadata_forensics
from backend.app.ml.image.ela_forensics import ela_forensics
from backend.app.ml.image.synthetic_detector import synthetic_detector


@pytest.fixture
def sample_test_image(tmp_path: Path) -> Path:
    img_path = tmp_path / "test_artifact.jpg"
    img = Image.new("RGB", (200, 200), color=(120, 150, 180))
    img.save(img_path, format="JPEG", quality=95)
    return img_path


@pytest.fixture
def sample_image_with_text(tmp_path: Path) -> Path:
    img_path = tmp_path / "test_with_text.png"
    img = Image.new("RGB", (250, 100), color=(240, 240, 240))
    meta = PngImagePlugin.PngInfo()
    meta.add_text("Comment", "NASA confirmed detection of water vapor on exoplanet.")
    img.save(img_path, format="PNG", pnginfo=meta)
    return img_path


def test_metadata_forensics(sample_test_image: Path):
    res = metadata_forensics.analyze(sample_test_image)
    assert "has_exif" in res
    assert "c2pa_present" in res
    assert "dimensions" in res
    assert res["dimensions"]["width"] == 200
    assert res["dimensions"]["height"] == 200
    assert res["format"] == "JPEG"
    assert res["color_mode"] == "RGB"
    assert isinstance(res["notes"], list)


def test_ela_forensics(sample_test_image: Path):
    res = ela_forensics.analyze(sample_test_image)
    assert "ela_max_error" in res
    assert "is_ela_spliced" in res
    assert "manipulation_signal" in res
    assert "score" in res["manipulation_signal"]
    assert "limitations" in res["manipulation_signal"]
    assert 0.0 <= res["ela_max_error"] <= 1.0


def test_synthetic_detector(sample_test_image: Path):
    res = synthetic_detector.analyze(sample_test_image)
    assert "synthetic_probability" in res
    assert "confidence" in res
    assert "model_name" in res
    assert "limitations" in res
    assert 0.0 <= res["synthetic_probability"] <= 1.0
    assert res["confidence"] in {"LOW", "MODERATE", "HIGH"}


def test_ocr_extraction_and_normalization(sample_image_with_text: Path, sample_test_image: Path):
    # Image with metadata text
    res = ocr_engine.extract_ocr(sample_image_with_text)
    assert "water vapor" in res["text"].lower() or len(res["text"]) > 0
    assert "confidence" in res
    assert isinstance(res["regions"], list)

    # Empty image without text
    empty_res = ocr_engine.extract_ocr(sample_test_image)
    assert isinstance(empty_res["text"], str)

    # Normalization helper
    norm = ocr_engine.normalize_ocr_text(" B   R E A K I N G \n\n  news   alert  ")
    assert "BREAKING" in norm
    assert "  " not in norm


@pytest.mark.asyncio
async def test_image_analyze_api_endpoint(sample_test_image: Path):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        with open(sample_test_image, "rb") as f:
            files = {"file": ("test_artifact.jpg", f, "image/jpeg")}
            res = await ac.post("/api/v1/image/analyze", files=files)
        assert res.status_code == 200
        data = res.json()
        assert "forensics" in data
        assert "overall_assessment" in data
        assert data["forensics"]["synthetic_probability"] >= 0.0


@pytest.mark.asyncio
async def test_verify_image_endpoint_empty_text(sample_test_image: Path):
    """Test POST /api/v1/verify/image for image without text -> INSUFFICIENT_EVIDENCE"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        with open(sample_test_image, "rb") as f:
            files = {"file": ("test_artifact.jpg", f, "image/jpeg")}
            res = await ac.post("/api/v1/verify/image", files=files)
        assert res.status_code == 200
        data = res.json()
        assert data["input_modality"] == "IMAGE"
        assert data["overall_veracity"] == "INSUFFICIENT_EVIDENCE"
        assert data["image_forensics"] is not None
        assert "executive_summary" in data


@pytest.mark.asyncio
async def test_verify_image_endpoint_with_text(sample_image_with_text: Path):
    """Test POST /api/v1/verify/image for image with text -> claim extraction & verification"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        with open(sample_image_with_text, "rb") as f:
            files = {"file": ("test_with_text.png", f, "image/png")}
            res = await ac.post("/api/v1/verify/image", files=files)
        assert res.status_code == 200
        data = res.json()
        assert data["input_modality"] == "IMAGE"
        assert data["image_forensics"] is not None
        assert "job_id" in data


@pytest.mark.asyncio
async def test_invalid_image_signature_rejected(tmp_path: Path):
    """Corrupted / fake image header must be rejected with 400"""
    corrupt_file = tmp_path / "corrupt.jpg"
    corrupt_file.write_bytes(b"NOT_A_JPEG_HEADER_AT_ALL_1234567890")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        with open(corrupt_file, "rb") as f:
            files = {"file": ("corrupt.jpg", f, "image/jpeg")}
            res = await ac.post("/api/v1/verify/image", files=files)
        assert res.status_code == 400
        assert "signature" in res.json()["detail"].lower()

