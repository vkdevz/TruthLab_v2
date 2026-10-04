from datetime import datetime, timezone
import hashlib
from backend.app.schemas.claim import AtomicClaim
from backend.app.schemas.evidence import EvidenceSnippet
from backend.app.schemas.verification import EvidenceGraph, GraphNode, GraphEdge, AuditTrail
from backend.app.schemas.explanation import VerificationAuditReport, CalibratedUncertainty
from backend.app.schemas.veracity import VeracityLabel, StanceType
from backend.app.ml.explainability.calibration import confidence_calibrator
from backend.app.ml.explainability.sufficiency import evidence_sufficiency_metric


class AuditReportGenerator:
    """Constructs interactive node-edge evidence graphs and auditable verification certificates."""

    def build_evidence_graph(
        self,
        claim: AtomicClaim,
        evidence_items: list[EvidenceSnippet],
        verdict: VeracityLabel
    ) -> EvidenceGraph:
        nodes = []
        edges = []

        # Claim Node
        claim_node_id = f"claim-{claim.id}"
        nodes.append(GraphNode(
            id=claim_node_id,
            label=f"Claim: {claim.canonical_claim[:50]}...",
            type="claim",
            status=verdict.value,
        ))

        seen_sources = set()

        for idx, ev in enumerate(evidence_items):
            ev_node_id = f"ev-{ev.id}"
            nodes.append(GraphNode(
                id=ev_node_id,
                label=f"Evidence: {ev.source_name} ({ev.stance.value})",
                type="evidence",
                status=ev.stance.value,
            ))

            # Edge from Evidence to Claim
            edges.append(GraphEdge(
                source=ev_node_id,
                target=claim_node_id,
                relation=ev.stance.value,
                weight=ev.retrieval_score,
            ))

            # Source Domain Node
            source_id = f"src-{hashlib.md5(ev.domain.encode()).hexdigest()[:6]}"
            if source_id not in seen_sources:
                seen_sources.add(source_id)
                nodes.append(GraphNode(
                    id=source_id,
                    label=ev.domain,
                    type="source",
                    status="VERIFIED" if ev.is_claim_review else "WEB",
                ))

            # Edge from Evidence to Source Domain
            edges.append(GraphEdge(
                source=ev_node_id,
                target=source_id,
                relation="CITES",
                weight=1.0,
            ))

        return EvidenceGraph(nodes=nodes, edges=edges)

    def generate_report(
        self,
        job_id: str,
        claim: AtomicClaim,
        evidence_items: list[EvidenceSnippet],
        verdict: VeracityLabel,
        raw_confidence: float,
        audit: AuditTrail,
    ) -> VerificationAuditReport:
        uncertainty = confidence_calibrator.calibrate(raw_confidence)
        sufficiency_idx, is_suff, suff_notes = evidence_sufficiency_metric.compute_sufficiency(evidence_items)
        graph = self.build_evidence_graph(claim, evidence_items, verdict)

        # Merge sufficiency notes into audit limitations
        combined_limitations = list(audit.limitations)
        if not is_suff:
            combined_limitations.extend(suff_notes)

        audit.limitations = list(dict.fromkeys(combined_limitations))

        return VerificationAuditReport(
            job_id=job_id,
            target_claim=claim.canonical_claim,
            verdict=verdict,
            uncertainty=uncertainty,
            sufficiency_index=sufficiency_idx,
            audit_trail=audit,
            evidence_graph=graph,
            export_timestamp=datetime.now(timezone.utc).isoformat(),
        )


audit_report_generator = AuditReportGenerator()
