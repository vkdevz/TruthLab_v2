from backend.app.schemas.evidence import EvidenceSnippet
from backend.app.schemas.veracity import StanceType
from backend.app.verification.nli import nli_interpreter, NLIEvidenceInterpreter


class StanceClassifier:
    """Predicts entailment, contradiction, or neutrality between a claim and an evidence snippet.
    Delegates to the canonical NLIEvidenceInterpreter to maintain a single source of truth."""

    def __init__(self, interpreter: NLIEvidenceInterpreter | None = None):
        self._interpreter = interpreter or nli_interpreter

    def predict_stance(self, claim_text: str, snippet_text: str) -> tuple[StanceType, dict[str, float]]:
        return self._interpreter.evaluate_relationship(claim_text, snippet_text)

    def evaluate_evidence_stances(self, claim_text: str, evidence_items: list[EvidenceSnippet]) -> list[EvidenceSnippet]:
        return self._interpreter.process_evidence_stances(claim_text, evidence_items)


stance_classifier = StanceClassifier()
