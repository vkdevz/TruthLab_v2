from datetime import datetime, timezone
import uuid
from typing import Optional, List
from fastapi import HTTPException

from backend.app.schemas.claim import AtomicClaim
from backend.app.schemas.evidence import EvidenceSnippet
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
from backend.app.ml.claim.decomposer import claim_decomposer
from backend.app.evidence.provider import composite_evidence_retriever
from backend.app.evidence.ranking import hybrid_evidence_ranker
from backend.app.verification.nli import nli_interpreter
from backend.app.verification.verdict_engine import verdict_engine
from backend.app.services.job_manager import job_manager


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PipelineService:
    """Core end-to-end verification pipeline orchestrator:
    TEXT / URL -> CLAIM -> EVIDENCE -> VERIFICATION -> EXPLANATION
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

    async def _execute_verification_pipeline(
        self,
        job_id: str,
        modality: ModalityType,
        content_text: str,
        source_meta: dict
    ) -> FullVerificationResponse:
        created_at = utc_now()

        # Stage 1: Claim Extraction & Decomposition
        await job_manager.update_progress(job_id, stage="CLAIM_EXTRACTION", percent=25)
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
                image_forensics=None,
                video_forensics=None,
                evidence_graph=empty_graph,
                executive_summary="No check-worthy factual claims could be extracted from the input text.",
                system_limitations=["Input text contains insufficient factual statements suitable for empirical verification."]
            )
            await job_manager.complete_job(job_id, resp.model_dump(mode="json"))
            return resp

        # Stage 2: Evidence Retrieval, Ranking & NLI per claim
        await job_manager.update_progress(job_id, stage="EVIDENCE_RETRIEVAL", percent=45)
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

            # Stage 5: Verdict & Sufficiency Determination
            result = verdict_engine.evaluate_veracity(
                claim=claim,
                evidence_items=stanced_evidence
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
            progress = 45 + int(35 * ((idx + 1) / total_claims))
            await job_manager.update_progress(job_id, stage="VERIFYING_CLAIMS", percent=progress)

        # Stage 6: Multi-Claim Aggregation & Explanation Synthesis
        await job_manager.update_progress(job_id, stage="SYNTHESIZING_EXPLANATION", percent=90)
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
            image_forensics=None,
            video_forensics=None,
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

        meta_title = source_meta.get("title")
        prefix = f"For article '{meta_title}': " if meta_title else ""

        if overall_veracity == VeracityLabel.CONTRADICTED:
            summary = f"{prefix}Material contradictions were identified across {contradicted_count} of {total} evaluated claim(s) by authoritative fact-checks and independent reporting."
        elif overall_veracity == VeracityLabel.SUPPORTED:
            summary = f"{prefix}All {total} factual proposition(s) are corroborated by credible reporting and official documentation."
        elif overall_veracity == VeracityLabel.OUTDATED:
            summary = f"{prefix}The content recirculates historical events or obsolete announcements presented out of their original temporal context."
        elif overall_veracity == VeracityLabel.MISLEADING:
            summary = f"{prefix}The content exhibits partial truths, context manipulation, or conflicting evidence across {misleading_count} statement(s)."
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
