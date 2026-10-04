from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.ml.video.ffmpeg_processor import ffmpeg_processor
from backend.app.ml.video.video_pipeline import video_pipeline


@pytest.fixture
def mock_video_file(tmp_path: Path) -> Path:
    # Create a small binary file simulating an MP4 file
    vid_path = tmp_path / "sample_test.mp4"
    # Write a simple MP4 header signature (ftypisom)
    mp4_signature = b"\x00\x00\x00\x20\x66\x74\x79\x70\x69\x73\x6f\x6d\x00\x00\x02\x00\x69\x73\x6f\x6d\x69\x73\x6f\x32\x61\x76\x63\x31\x6d\x70\x34\x31"
    vid_path.write_bytes(mp4_signature + b"\x00" * 2048)
    return vid_path


def test_ffmpeg_processor_detection():
    # Verify processor handles presence or absence of ffmpeg without raising unhandled exceptions
    has_ff = ffmpeg_processor.has_ffmpeg()
    assert isinstance(has_ff, bool)


@pytest.mark.asyncio
async def test_video_pipeline_orchestration(mock_video_file: Path):
    response = await video_pipeline.process_video(mock_video_file, "sample_test.mp4")
    assert response.filename == "sample_test.mp4"
    assert "unified_corpus" in response.model_dump()
    assert response.forensics.duration_seconds >= 0.0
    assert isinstance(response.verified_claims, list)


@pytest.mark.asyncio
async def test_video_analyze_api_endpoint(mock_video_file: Path):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        with open(mock_video_file, "rb") as f:
            files = {"file": ("sample_test.mp4", f, "video/mp4")}
            res = await ac.post("/api/v1/video/analyze", files=files)
        assert res.status_code == 200
        data = res.json()
        assert data["filename"] == "sample_test.mp4"
        assert "forensics" in data
        assert "overall_assessment" in data
