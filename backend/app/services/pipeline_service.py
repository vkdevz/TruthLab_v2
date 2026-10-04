from datetime import datetime, timezone
import tempfile
import shutil
import uuid
from pathlib import Path
from typing import Optional, List
from fastapi import HTTPException, UploadFile

from backend.app.schemas.claim import AtomicClaim
from backend.app.schemas.evidence import EvidenceSnippet
from backend.app.schemas.media import ImageForensicIndicators, VideoForensicIndicators
from backend.app.schemas.veracity import ModalityType, VeracityLabel, StanceType
from backend.app.schemas.verification import (
    FullVerificationResponse,
    ClaimVerificationResult,
    EvidenceGraph,
    GraphNode,
    GraphEdge,
    AuditTrail
)
from backend.app.ingestion.text_ingest import text_ingestion_service
from backend.app.ingestion.url_ingest import url_ingestion_service
from backend.app.services.storage import storage_service
from backend.app.ml.image.ocr_engine import ocr_engine
from backend.app.ml.image.metadata_forensics import metadata_forensics
from backend.app.ml.image.ela_forensics import ela_forensics
from backend.app.ml.image.synthetic_detector import synthetic_detector
from backend.app.ml.video.ffmpeg_processor import ffmpeg_processor
from backend.app.ml.video.transcriber import video_transcriber
from backend.app.ml.video.scene_extractor import scene_extractor
from backend.app.ml.claim.decomposer import claim_decomposer
from backend.app.evidence.provider import composite_evidence_retriever
from backend.app.evidence.ranking import hybrid_evidence_ranker
from backend.app.verification.nli import nli_interpreter
from backend.app.verification.verdict_engine import verdict_engine
from backend.app.services.job_manager import job_manager
from backend.app.core.config import settings


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PipelineService:
    """Core end-to-end verification pipeline orchestrator across all supported modalities:
    TEXT / URL / IMAGE / VIDEO -> CLAIM -> EVIDENCE -> TEMPORAL -> MEDIA -> FUSION -> EXPLANATION
    """

    async def verify_text(self, text: str) -> FullVerificationResponse:
        job_id = await job_manager.create_job(input_modality="TEXT", input_summary=text[:200])
        try:
            await job_manager.update_progress(job_id, stage="INGESTING", percent=10)
            cleaned_text = text_ingestion_service.ingest_text(text)

            return await self._execute_verification_pipeline(
                job_id=job_id,
                modality=ModalityType.TEXT,
                content_text=cleaned_text,
                source_meta={"type": "raw_text"}
            )
        except HTTPException:
            raise
        except Exception as exc:
            await job_manager.fail_job(job_id, error_message=str(exc))
            raise HTTPException(status_code=500, detail=f"Pipeline verification failure: {str(exc)}")

    async def verify_url(self, url: str) -> FullVerificationResponse:
        job_id = await job_manager.create_job(input_modality="URL", input_summary=url)
        try:
            await job_manager.update_progress(job_id, stage="FETCHING_URL", percent=10)
            article_data = await url_ingestion_service.ingest_url(url)
            article_text = article_data["text"]

            return await self._execute_verification_pipeline(
                job_id=job_id,
                modality=ModalityType.URL,
                content_text=article_text,
                source_meta=article_data
            )
        except HTTPException:
            raise
        except Exception as exc:
            await job_manager.fail_job(job_id, error_message=str(exc))
            raise HTTPException(status_code=500, detail=f"Pipeline URL verification failure: {str(exc)}")

    async def verify_image(self, file: UploadFile) -> FullVerificationResponse:
        job_id = await job_manager.create_job(input_modality="IMAGE", input_summary=file.filename or "image_upload")
        saved_path = await storage_service.save_upload_file(file, is_video=False)

        try:
            await job_manager.update_progress(job_id, stage="ANALYZING_IMAGE", percent=15)

            # 1. OCR Extraction
            ocr_res = ocr_engine.extract_ocr(saved_path)
            ocr_text = ocr_res.get("text", "")
            has_text = bool(ocr_text and len(ocr_text.strip()) > 5)

            # 2. Forensic Analysis
            meta_res = metadata_forensics.analyze(saved_path)
            ela_res = ela_forensics.analyze(saved_path)
            synth_res = synthetic_detector.analyze(saved_path)

            all_notes = meta_res.get("notes", []) + ela_res.get("notes", []) + synth_res.get("notes", [])

            image_forensics = ImageForensicIndicators(
                has_exif=meta_res.get("has_exif", False),
                software_tag=meta_res.get("software_tag"),
                c2pa_present=meta_res.get("c2pa_present", False),
                ela_max_error=ela_res.get("ela_max_error", 0.0),
                is_ela_spliced=ela_res.get("is_ela_spliced", False),
                synthetic_probability=synth_res.get("synthetic_probability", 0.15),
                synthetic_confidence=synth_res.get("confidence", "LOW"),
                forensic_notes=all_notes,
            )

            # 3. If image contains no legible text, return INSUFFICIENT_EVIDENCE with forensics
            if not has_text:
                created_at = utc_now()
                empty_graph = EvidenceGraph(nodes=[], edges=[])
                summary = (
                    "Visual image inspected. No legible textual claims or verifiable statements "
                    "could be extracted from the image. Forensic indicators computed."
                )
                resp = FullVerificationResponse(
                    job_id=job_id,
                    created_at=created_at,
                    completed_at=utc_now(),
                    input_modality=ModalityType.IMAGE,
                    overall_veracity=VeracityLabel.INSUFFICIENT_EVIDENCE,
                    overall_confidence=0.50,
                    claims_verified=[],
                    image_forensics=image_forensics,
                    video_forensics=None,
                    evidence_graph=empty_graph,
                    executive_summary=summary,
                    system_limitations=[
                        "Image contains little or no testable text. The system withholds factual verification without check-worthy claims."
                    ],
                )
                await job_manager.complete_job(job_id, resp.model_dump(mode="json"))
                return resp

            # 4. Image contains text: execute multimodal verification pipeline
            return await self._execute_verification_pipeline(
                job_id=job_id,
                modality=ModalityType.IMAGE,
                content_text=ocr_text,
                source_meta={"filename": file.filename, "ocr_confidence": ocr_res.get("confidence")},
                image_forensics=image_forensics,
                ocr_text=ocr_text,
            )

        except HTTPException:
            await job_manager.fail_job(job_id, error_message="HTTP exception during image verification")
            raise
        except Exception as exc:
            await job_manager.fail_job(job_id, error_message=str(exc))
            raise HTTPException(status_code=500, detail=f"Image verification failure: {str(exc)}")
        finally:
            storage_service.cleanup_file(saved_path)

    async def verify_video(self, file: UploadFile) -> FullVerificationResponse:
        job_id = await job_manager.create_job(input_modality="VIDEO", input_summary=file.filename or "video_upload")
        saved_path = await storage_service.save_upload_file(file, is_video=True)
        scratch_dir = Path(tempfile.mkdtemp(prefix="video_pipe_"))

        try:
            await job_manager.update_progress(job_id, stage="PROBING_VIDEO", percent=10)
            probe_meta = await ffmpeg_processor.probe_metadata(saved_path)
            duration = probe_meta.get("duration_seconds", 0.0)

            # Check video duration limit
            if duration > settings.MAX_VIDEO_DURATION_SECONDS:
                raise HTTPException(
                    status_code=413,
                    detail=f"Video duration ({duration:.1f}s) exceeds maximum allowed {settings.MAX_VIDEO_DURATION_SECONDS}s."
                )

            # 1. Audio track extraction & speech-to-text
            await job_manager.update_progress(job_id, stage="TRANSCRIBING_AUDIO", percent=20)
            wav_path = scratch_dir / "audio.wav"
            has_audio = await ffmpeg_processor.extract_audio_wav(saved_path, wav_path)

            transcript = ""
            if has_audio and wav_path.exists():
                asr_res = video_transcriber.transcribe(wav_path)
                transcript = asr_res.get("transcript", "")

            # 2. Keyframe sampling & visual overlay OCR
            await job_manager.update_progress(job_id, stage="EXTRACTING_KEYFRAMES", percent=35)
            frames_dir = scratch_dir / "frames"
            frames, overlay_ocr, frame_findings = await scene_extractor.extract_and_analyze_scenes(
                saved_path, frames_dir
            )

            # 3. Aggregate keyframe forensics
            avg_synth = 0.15
            if frame_findings:
                synth_vals = [f["synthetic_probability"] for f in frame_findings]
                avg_synth = float(round(sum(synth_vals) / len(synth_vals), 3))

            fps = probe_meta.get("frame_rate", 30.0)
            total_frames = int(duration * fps) if duration > 0 and fps > 0 else (len(frames) * 120 or 240)

            video_forensics = VideoForensicIndicators(
                duration_seconds=duration if duration > 0 else (float(len(frames) * 4) if frames else 10.0),
                total_frames=total_frames,
                extracted_scenes=len(frames),
                has_audio_track=probe_meta.get("has_audio", False) or has_audio,
                inconsistent_frame_rate=False,
                synthetic_face_probability=avg_synth,
            )

            # 4. Formulate unified corpus from speech and overlay text
            corpus_parts = []
            if transcript:
                corpus_parts.append(f"Spoken dialogue: {transcript}")
            if overlay_ocr:
                corpus_parts.append(f"Visual text on screen: {overlay_ocr}")

            has_content = bool(corpus_parts)
            combined_corpus = " \n ".join(corpus_parts) if has_content else ""

            if not has_content:
                created_at = utc_now()
                empty_graph = EvidenceGraph(nodes=[], edges=[])
                summary = (
                    "Video clip inspected. No audible speech dialogue or legible text overlays "
                    "could be extracted for factual claim verification."
                )
                resp = FullVerificationResponse(
                    job_id=job_id,
                    created_at=created_at,
                    completed_at=utc_now(),
                    input_modality=ModalityType.VIDEO,
                    overall_veracity=VeracityLabel.INSUFFICIENT_EVIDENCE,
                    overall_confidence=0.50,
                    claims_verified=[],
                    image_forensics=None,
                    video_forensics=video_forensics,
                    evidence_graph=empty_graph,
                    executive_summary=summary,
                    system_limitations=[
                        "Video contains no testable spoken claims or legible text overlays suitable for factual verification."
                    ],
                )
                await job_manager.complete_job(job_id, resp.model_dump(mode="json"))
                return resp

            # 5. Execute multimodal claim verification
            return await self._execute_verification_pipeline(
                job_id=job_id,
                modality=ModalityType.VIDEO,
                content_text=combined_corpus,
                source_meta={
                    "filename": file.filename,
                    "duration": video_forensics.duration_seconds,
                    "extracted_scenes": video_forensics.extracted_scenes,
                },
                video_forensics=video_forensics,
                ocr_text=overlay_ocr,
            )

        except HTTPException:
            await job_manager.fail_job(job_id, error_message="HTTP exception during video verification")
            raise
        except Exception as exc:
            await job_manager.fail_job(job_id, error_message=str(exc))
            raise HTTPException(status_code=500, detail=f"Video verification failure: {str(exc)}")
        finally:
            storage_service.cleanup_file(saved_path)
            shutil.rmtree(scratch_dir, ignore_errors=True)

    async def _execute_verification_pipeline(
        self,
        job_id: str,
        modality: ModalityType,
        content_text: str,
        source_meta: dict,
        image_forensics: Optional[ImageForensicIndicators] = None,
        video_forensics: Optional[VideoForensicIndicators] = None,
        ocr_text: Optional[str] = None,
    ) -> FullVerificationResponse:
        created_at = utc_now()

        # Stage 1: Claim Extraction & Decomposition
        await job_manager.update_progress(job_id, stage="CLAIM_EXTRACTION", percent=50)
        claims = claim_decomposer.decompose(content_text)

        # Fallback if text is concise single statement
        if not claims and len(content_text.strip().split()) >= 3:
            claim_id = f"c-{uuid.uuid4().hex[:8]}"
            single_claim = AtomicClaim(
                id=claim_id,
                raw_text=content_text.strip(),
                canonical_claim=content_text.strip(),
                checkworthy_score=0.75,
                is_checkworthy=True,
                entities=[],
                temporal_anchor=None,
                inferred_date=None,
                search_queries=[content_text.strip()],
            )
            claims = [single_claim]

        if not claims:
            # No verifiable factual claims found in content
            empty_graph = EvidenceGraph(nodes=[], edges=[])
            resp = FullVerificationResponse(
                job_id=job_id,
                created_at=created_at,
                completed_at=utc_now(),
                input_modality=modality,
                overall_veracity=VeracityLabel.INSUFFICIENT_EVIDENCE,
                overall_confidence=0.50,
                claims_verified=[],
                image_forensics=image_forensics,
                video_forensics=video_forensics,
                evidence_graph=empty_graph,
                executive_summary="No check-worthy factual claims could be extracted from the input text.",
                system_limitations=["Input text contains insufficient factual statements suitable for empirical verification."]
            )
            await job_manager.complete_job(job_id, resp.model_dump(mode="json"))
            return resp

        # Stage 2: Evidence Retrieval, Ranking & NLI per claim
        await job_manager.update_progress(job_id, stage="EVIDENCE_RETRIEVAL", percent=65)
        verified_results: List[ClaimVerificationResult] = []
        graph_nodes: List[GraphNode] = []
        graph_edges: List[GraphEdge] = []

        total_claims = len(claims)
        for idx, claim in enumerate(claims):
            # Query candidate evidence
            raw_candidates = await composite_evidence_retriever.retrieve_candidate_evidence(
                claim_id=claim.id,
                canonical_claim=claim.canonical_claim,
                search_queries=claim.search_queries,
                per_query_limit=4
            )

            # Stage 3: Evidence Ranking
            ranked_evidence = hybrid_evidence_ranker.rank_evidence(
                claim_text=claim.canonical_claim,
                candidate_evidence=raw_candidates,
                top_k=5
            )

            # Stage 4: NLI Relationship Interpretation
            stanced_evidence = nli_interpreter.process_evidence_stances(
                claim_text=claim.canonical_claim,
                evidence_items=ranked_evidence
            )

            # Stage 5: Verdict & Sufficiency Determination (Multimodal Late-Fusion)
            result = verdict_engine.evaluate_veracity(
                claim=claim,
                evidence_items=stanced_evidence,
                image_forensics=image_forensics,
                video_forensics=video_forensics,
                ocr_text=ocr_text,
            )
            verified_results.append(result)

            # Build Graph Nodes & Edges
            c_node_id = f"node-{claim.id}"
            graph_nodes.append(GraphNode(
                id=c_node_id,
                label=claim.canonical_claim[:40] + ("..." if len(claim.canonical_claim) > 40 else ""),
                type="claim",
                status=result.veracity.value
            ))

            for ev in result.evidence_items:
                ev_node_id = f"node-{ev.id}"
                graph_nodes.append(GraphNode(
                    id=ev_node_id,
                    label=ev.source_name,
                    type="evidence",
                    status=ev.stance.value
                ))
                graph_edges.append(GraphEdge(
                    source=ev_node_id,
                    target=c_node_id,
                    relation=ev.stance.value,
                    weight=ev.retrieval_score
                ))

            # Update progress incrementally
            progress = 65 + int(25 * ((idx + 1) / total_claims))
            await job_manager.update_progress(job_id, stage="VERIFYING_CLAIMS", percent=progress)

        # Stage 6: Multi-Claim Aggregation & Explanation Synthesis
        await job_manager.update_progress(job_id, stage="SYNTHESIZING_EXPLANATION", percent=92)
        overall_veracity, overall_confidence = self._aggregate_overall_veracity(verified_results)
        summary, limitations = self._generate_explanation(overall_veracity, verified_results, source_meta)

        evidence_graph = EvidenceGraph(
            nodes=self._deduplicate_nodes(graph_nodes),
            edges=graph_edges
        )

        completed_at = utc_now()
        full_response = FullVerificationResponse(
            job_id=job_id,
            created_at=created_at,
            completed_at=completed_at,
            input_modality=modality,
            overall_veracity=overall_veracity,
            overall_confidence=round(overall_confidence, 3),
            claims_verified=verified_results,
            image_forensics=image_forensics,
            video_forensics=video_forensics,
            ocr_text=ocr_text,
            transcript_text=source_meta.get("transcript") or (content_text if modality == ModalityType.VIDEO and not ocr_text else None),
            evidence_graph=evidence_graph,
            executive_summary=summary,
            system_limitations=limitations
        )


        await job_manager.complete_job(job_id, full_response.model_dump(mode="json"))
        return full_response

    def _aggregate_overall_veracity(
        self,
        results: List[ClaimVerificationResult]
    ) -> tuple[VeracityLabel, float]:
        if not results:
            return VeracityLabel.INSUFFICIENT_EVIDENCE, 0.50

        verdicts = [r.veracity for r in results]
        confidences = [r.confidence for r in results]
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.50

        # Precedence: CONTRADICTED > OUTDATED > MISLEADING > SUPPORTED > INSUFFICIENT_EVIDENCE
        if VeracityLabel.CONTRADICTED in verdicts:
            return VeracityLabel.CONTRADICTED, min(0.96, avg_conf)
        if VeracityLabel.OUTDATED in verdicts:
            return VeracityLabel.OUTDATED, min(0.95, avg_conf)
        if VeracityLabel.MISLEADING in verdicts:
            return VeracityLabel.MISLEADING, min(0.90, avg_conf)
        if all(v == VeracityLabel.SUPPORTED for v in verdicts):
            return VeracityLabel.SUPPORTED, min(0.95, avg_conf)
        if all(v == VeracityLabel.INSUFFICIENT_EVIDENCE for v in verdicts):
            return VeracityLabel.INSUFFICIENT_EVIDENCE, 0.45

        # Mixed support/insufficient
        return VeracityLabel.MISLEADING, round(avg_conf, 3)

    def _generate_explanation(
        self,
        overall_veracity: VeracityLabel,
        results: List[ClaimVerificationResult],
        source_meta: dict
    ) -> tuple[str, List[str]]:
        total = len(results)
        supported_count = sum(1 for r in results if r.veracity == VeracityLabel.SUPPORTED)
        contradicted_count = sum(1 for r in results if r.veracity == VeracityLabel.CONTRADICTED)
        misleading_count = sum(1 for r in results if r.veracity == VeracityLabel.MISLEADING)
        outdated_count = sum(1 for r in results if r.veracity == VeracityLabel.OUTDATED)
        insufficient_count = sum(1 for r in results if r.veracity == VeracityLabel.INSUFFICIENT_EVIDENCE)

        meta_title = source_meta.get("title") or source_meta.get("filename")
        prefix = f"For media input '{meta_title}': " if meta_title else ""

        if overall_veracity == VeracityLabel.CONTRADICTED:
            summary = f"{prefix}Material contradictions were identified across {contradicted_count} of {total} evaluated claim(s) by authoritative fact-checks and independent reporting."
        elif overall_veracity == VeracityLabel.SUPPORTED:
            summary = f"{prefix}All {total} factual proposition(s) are corroborated by credible reporting and official documentation."
        elif overall_veracity == VeracityLabel.OUTDATED:
            summary = f"{prefix}The content recirculates historical events or obsolete announcements presented out of their original temporal context."
        elif overall_veracity == VeracityLabel.MISLEADING:
            summary = f"{prefix}The content exhibits partial truths, context manipulation, or cross-modal disparity across {misleading_count} statement(s)."
        else:
            summary = f"{prefix}Available evidentiary sources provide insufficient data to reach a conclusive empirical determination."

        limitations = [
            "Verification is grounded strictly in indexed fact-checking corpora and authoritative public web sources available at query time.",
            "NLI and stance scoring represent probabilistic evidence interpretation, not absolute infallible ground truth.",
            "Predictions should be considered decision-support tools alongside human journalistic evaluation."
        ]
        return summary, limitations

    def _deduplicate_nodes(self, nodes: List[GraphNode]) -> List[GraphNode]:
        seen = set()
        deduped = []
        for n in nodes:
            if n.id not in seen:
                seen.add(n.id)
                deduped.append(n)
        return deduped


pipeline_service = PipelineService()

