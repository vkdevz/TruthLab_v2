from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.app.ml.baseline.classifier import baseline_classifier

router = APIRouter(prefix="/baseline", tags=["Baseline Fake-News Classifier"])


class BaselinePredictRequest(BaseModel):
    text: str = Field(..., min_length=5, description="Input claim or text fragment to evaluate using lexical baseline")


class LexicalCue(BaseModel):
    term: str
    weight: float
    direction: str


class BaselinePredictResponse(BaseModel):
    label: str  # "REAL" or "FAKE"
    confidence: float
    fake_probability: float
    real_probability: float
    top_predictive_cues: list[LexicalCue]
    explanation: str
    baseline_disclaimer: str = (
        "This baseline makes predictions solely from lexical phrasing styles. "
        "It does NOT retrieve evidence or verify factual reality."
    )


@router.post("/predict", response_model=BaselinePredictResponse)
async def predict_baseline(payload: BaselinePredictRequest):
    try:
        prediction = baseline_classifier.predict(payload.text)
        return BaselinePredictResponse(
            label=prediction.label,
            confidence=prediction.confidence,
            fake_probability=prediction.fake_probability,
            real_probability=prediction.real_probability,
            top_predictive_cues=[
                LexicalCue(term=str(cue["term"]), weight=float(cue["weight"]), direction=str(cue["direction"]))
                for cue in prediction.top_predictive_cues
            ],
            explanation=prediction.explanation,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Baseline inference error: {str(exc)}")
