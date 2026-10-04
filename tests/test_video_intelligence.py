from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.ml.video.ffmpeg_processor import ffmpeg_processor
from backend.app.ml.video.transcriber import video_transcriber
from backend.app.ml.video.video_pipeline import video_pipeline


@pytest.fixture
def mock_video_file(tmp_path: Path) -> Path:
    vid_path = tmp_path / "sample_test.mp4"
    # Write a simple valid MP4 header signature (ftypisom)
    mp4_signature = b"\x00\x00\x00\x20\x66\x74\x79\x70\x69\x73\x6f\x6d\x00\x00\x02\x00\x69\x73\x6f\x6d\x69\x73\x6f\x32\x61\x76\x63\x31\x6d\x70\x34\x31"
    vid_path.write_bytes(mp4_signature + b"\x00" * 4096)
    return vid_path


def test_ffmpeg_processor_detection():
    has_ff = ffmpeg_processor.has_ffmpeg()
    assert isinstance(has_ff, bool)


@pytest.mark.asyncio
async def test_ffmpeg_probe_metadata(mock_video_file: Path):
    meta = await ffmpeg_processor.probe_metadata(mock_video_file)
    assert "duration_seconds" in meta
    assert "width" in meta
    assert "height" in meta
    assert "codec" in meta
    assert "has_audio" in meta
    assert isinstance(meta["notes"], list)


def test_video_transcriber_interface(tmp_path: Path):
    # Test ASR interface with missing file or fallback
    dummy_audio = tmp_path / "silent.wav"
    dummy_audio.write_bytes(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00" + b"\x00" * 100)
    res = video_transcriber.transcribe(dummy_audio)
    assert "transcript" in res
    assert "segments" in res
    assert isinstance(res["segments"], list)


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


@pytest.mark.asyncio
async def test_verify_video_endpoint(mock_video_file: Path):
    """Test POST /api/v1/verify/video returning FullVerificationResponse"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        with open(mock_video_file, "rb") as f:
            files = {"file": ("sample_test.mp4", f, "video/mp4")}
            res = await ac.post("/api/v1/verify/video", files=files)
        assert res.status_code == 200
        data = res.json()
        assert data["input_modality"] == "VIDEO"
        assert "overall_veracity" in data
        assert data["video_forensics"] is not None
        assert "executive_summary" in data


@pytest.mark.asyncio
async def test_invalid_video_signature_rejected(tmp_path: Path):
    """Invalid video header must be rejected with 400"""
    bad_vid = tmp_path / "fake.mp4"
    bad_vid.write_bytes(b"INVALID_SIGNATURE_FOR_VIDEO_12345")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        with open(bad_vid, "rb") as f:
            files = {"file": ("fake.mp4", f, "video/mp4")}
            res = await ac.post("/api/v1/verify/video", files=files)
        assert res.status_code == 400
        assert "signature" in res.json()["detail"].lower()

