from backend.app.schemas.evidence import EvidenceSnippet
from backend.app.schemas.claim import AtomicClaim
from backend.app.schemas.verification import ClaimVerificationResult
from backend.app.schemas.media import ImageForensicIndicators, VideoForensicIndicators
from backend.app.verification.verdict_engine import verdict_engine, FiveClassVerdictEngine


class VeracityScorer:
    """Aggregates stances, computes evidence sufficiency, performs temporal integrity checks,
    and assigns calibrated veracity verdicts according to the 5-veracity taxonomy.
    Delegates to the canonical FiveClassVerdictEngine to maintain consistency across the codebase."""

    def __init__(self, engine: FiveClassVerdictEngine | None = None):
        self._engine = engine or verdict_engine

    def score_claim(
        self,
        claim: AtomicClaim,
        evidence_items: list[EvidenceSnippet],
        image_forensics: ImageForensicIndicators | None = None,
        video_forensics: VideoForensicIndicators | None = None,
        ocr_text: str | None = None,
    ) -> ClaimVerificationResult:
        return self._engine.evaluate_veracity(
            claim=claim,
            evidence_items=evidence_items,
            image_forensics=image_forensics,
            video_forensics=video_forensics,
            ocr_text=ocr_text,
        )


veracity_scorer = VeracityScorer()
