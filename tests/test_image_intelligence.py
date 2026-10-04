import io
from pathlib import Path
import pytest
from PIL import Image
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.ml.image.metadata_forensics import metadata_forensics
from backend.app.ml.image.ela_forensics import ela_forensics
from backend.app.ml.image.synthetic_detector import synthetic_detector


@pytest.fixture
def sample_test_image(tmp_path: Path) -> Path:
    img_path = tmp_path / "test_artifact.jpg"
    img = Image.new("RGB", (200, 200), color=(120, 150, 180))
    img.save(img_path, format="JPEG", quality=95)
    return img_path


def test_metadata_forensics(sample_test_image: Path):
    res = metadata_forensics.analyze(sample_test_image)
    assert "has_exif" in res
    assert "c2pa_present" in res
    assert isinstance(res["notes"], list)


def test_ela_forensics(sample_test_image: Path):
    res = ela_forensics.analyze(sample_test_image)
    assert "ela_max_error" in res
    assert "is_ela_spliced" in res
    assert 0.0 <= res["ela_max_error"] <= 1.0


def test_synthetic_detector(sample_test_image: Path):
    res = synthetic_detector.analyze(sample_test_image)
    assert "synthetic_probability" in res
    assert "confidence" in res
    assert 0.0 <= res["synthetic_probability"] <= 1.0
    assert res["confidence"] in {"LOW", "MODERATE", "HIGH"}


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
