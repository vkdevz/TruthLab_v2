import time
import io
import json
from pathlib import Path
from PIL import Image

from backend.app.services.storage import storage_service
from backend.app.ml.image.metadata_forensics import metadata_forensics
from backend.app.ml.image.ela_forensics import ela_forensics
from backend.app.ml.image.synthetic_detector import synthetic_detector
from backend.app.ml.image.ocr_engine import ocr_engine
from backend.app.ml.video.ffmpeg_processor import ffmpeg_processor
from backend.app.ml.video.transcriber import video_transcriber
from backend.app.ml.video.scene_extractor import scene_extractor
import asyncio
from backend.app.evidence.provider import composite_evidence_retriever
from backend.app.ml.fusion.fusion_model import multimodal_fusion_model
from backend.app.schemas.claim import AtomicClaim
from backend.app.schemas.veracity import ModalityType
from backend.app.services.pipeline_service import pipeline_service


def profile():
    profile_results = {}
    print("Starting Phase 2 Performance Profiling...")

    # 1. Prepare sample image in memory
    img = Image.new("RGB", (640, 480), color=(240, 240, 240))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG", quality=90)
    img_data = img_bytes.getvalue()

    # Image Ingestion (Save & Magic byte check)
    from fastapi import UploadFile
    t0 = time.perf_counter()
    upload_img = UploadFile(
        file=io.BytesIO(img_data),
        filename="benchmark_test.jpg",
        headers={"content-type": "image/jpeg"}
    )
    saved_img_path = asyncio.run(storage_service.save_upload_file(upload_img, is_video=False))
    profile_results["image_ingestion_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # Metadata Forensics
    t0 = time.perf_counter()
    meta = metadata_forensics.analyze(saved_img_path)
    profile_results["image_metadata_extraction_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # ELA Forensics
    t0 = time.perf_counter()
    ela = ela_forensics.analyze(saved_img_path)
    profile_results["image_ela_analysis_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # Synthetic Media Detector
    t0 = time.perf_counter()
    synth = synthetic_detector.analyze(saved_img_path)
    profile_results["image_synthetic_detector_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # OCR Engine
    t0 = time.perf_counter()
    ocr_res = ocr_engine.extract_ocr(saved_img_path)
    profile_results["image_ocr_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # Total Image Analysis (combined)
    profile_results["image_analysis_pipeline_ms"] = round(
        profile_results["image_metadata_extraction_ms"] +
        profile_results["image_ela_analysis_ms"] +
        profile_results["image_synthetic_detector_ms"] +
        profile_results["image_ocr_ms"], 2
    )

    # 2. Video Pipeline operations
    # Create sample MP4 container bytes (magic ftyp)
    mp4_bytes = (
        b"\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2avc1mp41"
        b"\x00\x00\x00\x08free"
        b"\x00\x00\x00\x10mdat" + b"A" * 1024
    )
    t0 = time.perf_counter()
    upload_vid = UploadFile(
        file=io.BytesIO(mp4_bytes),
        filename="benchmark_test.mp4",
        headers={"content-type": "video/mp4"}
    )
    saved_vid_path = asyncio.run(storage_service.save_upload_file(upload_vid, is_video=True))
    profile_results["video_ingestion_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # Video Probe
    t0 = time.perf_counter()
    probe = asyncio.run(ffmpeg_processor.probe_metadata(saved_vid_path))
    profile_results["video_probe_metadata_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # Video Keyframe Extraction
    t0 = time.perf_counter()
    import tempfile
    with tempfile.TemporaryDirectory() as kf_dir:
        keyframes = asyncio.run(ffmpeg_processor.extract_keyframes_with_timestamps(saved_vid_path, output_dir=kf_dir, max_frames=3))
    profile_results["video_keyframe_extraction_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # Video ASR
    t0 = time.perf_counter()
    trans = video_transcriber.transcribe(saved_vid_path)
    profile_results["video_asr_transcribe_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # Video Scene Extractor (OCR + forensics on frames)
    t0 = time.perf_counter()
    with tempfile.TemporaryDirectory() as sc_dir:
        frames_list, combined_ocr, scene_findings = asyncio.run(
            scene_extractor.extract_and_analyze_scenes(saved_vid_path, scratch_dir=sc_dir)
        )
    profile_results["video_frame_ocr_and_visual_analysis_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # 3. Evidence Retrieval
    test_claim = AtomicClaim(
        id="c-perf",
        raw_text="NASA Perseverance rover confirmed ancient lake sediments on Mars",
        canonical_claim="NASA Perseverance rover confirmed ancient lake sediments on Mars",
        checkworthy_score=0.95,
        is_checkworthy=True
    )
    t0 = time.perf_counter()
    evidence_items = asyncio.run(composite_evidence_retriever.retrieve_candidate_evidence(
        claim_id=test_claim.id,
        canonical_claim=test_claim.canonical_claim,
        search_queries=[test_claim.canonical_claim]
    ))
    profile_results["evidence_retrieval_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # 4. Multimodal Fusion
    t0 = time.perf_counter()
    fusion_dec = multimodal_fusion_model.fuse(
        claim=test_claim,
        evidence_items=evidence_items,
        image_forensics=None,
        ocr_text="Mars lake rover landing news"
    )
    profile_results["multimodal_fusion_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # 5. Full Pipeline End-to-End Image Latency
    test_img_upload = UploadFile(
        file=io.BytesIO(img_data),
        filename="benchmark_pipeline_test.jpg",
        headers={"content-type": "image/jpeg"}
    )
    t0 = time.perf_counter()
    img_resp = asyncio.run(pipeline_service.verify_image(test_img_upload))
    profile_results["total_image_pipeline_latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # 6. Full Pipeline End-to-End Video Latency
    test_vid_upload = UploadFile(
        file=io.BytesIO(mp4_bytes),
        filename="benchmark_pipeline_test.mp4",
        headers={"content-type": "video/mp4"}
    )
    t0 = time.perf_counter()
    vid_resp = asyncio.run(pipeline_service.verify_video(test_vid_upload))
    profile_results["total_video_pipeline_latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # Cleanup storage
    storage_service.cleanup_file(saved_img_path)
    storage_service.cleanup_file(saved_vid_path)

    out_path = Path("docs/experiments/pipeline_latency.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(profile_results, indent=2))
    print(f"Saved profile measurements to {out_path}:")
    print(json.dumps(profile_results, indent=2))


if __name__ == "__main__":
    profile()
