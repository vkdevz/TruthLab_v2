import shutil
import tempfile
from pathlib import Path
from backend.app.ml.video.ffmpeg_processor import ffmpeg_processor
from backend.app.ml.video.transcriber import video_transcriber
from backend.app.ml.video.scene_extractor import scene_extractor
from backend.app.ml.claim.decomposer import claim_decomposer
from backend.app.services.retrieval.web_retriever import web_retriever
from backend.app.services.retrieval.reranker import evidence_reranker
from backend.app.ml.nli.stance_classifier import stance_classifier
from backend.app.ml.nli.veracity_scorer import veracity_scorer
from backend.app.schemas.video_analysis import VideoAnalysisResponse
from backend.app.schemas.media import VideoForensicIndicators
from backend.app.schemas.verification import ClaimVerificationResult


class VideoVerificationPipeline:
    """Orchestrates end-to-end multimodal verification of video inputs using speech,
    visual text overlays, scene keyframes, and evidentiary retrieval."""

    async def process_video(self, video_path: Path | str, original_filename: str) -> VideoAnalysisResponse:
        v_path = Path(video_path)
        scratch_dir = Path(tempfile.mkdtemp(prefix="video_proc_"))

        try:
            # 1. Probe video technical metadata
            probe_meta = await ffmpeg_processor.probe_metadata(v_path)
            duration = probe_meta.get("duration_seconds", 0.0)
            has_audio_track = probe_meta.get("has_audio", False)

            # 2. Audio extraction and speech transcription (ASR)
            wav_path = scratch_dir / "audio_track.wav"
            has_audio = await ffmpeg_processor.extract_audio_wav(v_path, wav_path)

            transcript = ""
            asr_segments = []
            if has_audio and wav_path.exists():
                asr_result = video_transcriber.transcribe(wav_path)
                transcript = asr_result.get("transcript", "")
                asr_segments = asr_result.get("segments", [])

            # 3. Keyframe sampling and OCR text extraction
            frames_dir = scratch_dir / "frames"
            frames, overlay_ocr, frame_findings = await scene_extractor.extract_and_analyze_scenes(v_path, frames_dir)

            # 4. Formulate unified textual corpus from dialogue and screen text
            corpus_parts = []
            if transcript:
                corpus_parts.append(f"Spoken dialogue: {transcript}")
            if overlay_ocr:
                corpus_parts.append(f"Visual text on screen: {overlay_ocr}")

            combined_corpus = (
                " \n ".join(corpus_parts)
                if corpus_parts
                else "No spoken dialogue or legible text overlays extracted from video."
            )

            # 5. Extract and verify claims
            verified_claims: list[ClaimVerificationResult] = []
            if corpus_parts:
                claims = claim_decomposer.decompose(combined_corpus)
                for c in claims:
                    raw_ev = await web_retriever.retrieve_evidence(c.id, c.canonical_claim, c.search_queries)
                    reranked_ev = evidence_reranker.rerank(c.canonical_claim, raw_ev)
                    stanced_ev = stance_classifier.evaluate_evidence_stances(c.canonical_claim, reranked_ev)
                    result = veracity_scorer.score_claim(c, stanced_ev)
                    verified_claims.append(result)

            # 6. Aggregate visual manipulation heuristics across keyframes
            avg_synth = 0.15
            if frame_findings:
                synth_scores = [f["synthetic_probability"] for f in frame_findings]
                avg_synth = float(round(sum(synth_scores) / len(synth_scores), 3))

            fps = probe_meta.get("frame_rate", 30.0)
            total_frames = int(duration * fps) if duration > 0 and fps > 0 else (len(frames) * 120 or 240)

            forensics = VideoForensicIndicators(
                duration_seconds=duration if duration > 0 else (float(len(frames) * 4) if frames else 10.0),
                total_frames=total_frames,
                extracted_scenes=len(frames),
                has_audio_track=has_audio_track or has_audio,
                inconsistent_frame_rate=False,
                synthetic_face_probability=avg_synth,
            )

            assessment = (
                f"Video analysis extracted {len(frames)} representative scene keyframe(s), "
                f"sampled speech/overlay text ({len(combined_corpus.split())} words), "
                f"and verified {len(verified_claims)} testable proposition(s)."
            )

            return VideoAnalysisResponse(
                filename=original_filename,
                duration_seconds=forensics.duration_seconds,
                transcript_text=transcript if transcript else None,
                extracted_keyframes_count=len(frames),
                overlay_ocr_text=overlay_ocr if overlay_ocr else None,
                unified_corpus=combined_corpus,
                forensics=forensics,
                verified_claims=verified_claims,
                overall_assessment=assessment,
            )

        finally:
            shutil.rmtree(scratch_dir, ignore_errors=True)


video_pipeline = VideoVerificationPipeline()

