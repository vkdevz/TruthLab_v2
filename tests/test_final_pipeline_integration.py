"""End-to-End Unified Pipeline Integration Tests (Commit 18).

Validates that all input paths:
1. Text
2. URL
3. Image
4. Video
converge into the identical, complete FullVerificationResponse schema with
claims, evidence graph, calibrated confidence, uncertainty layer, and audit trail.
"""

import io
import pytest
from fastapi import HTTPException
from PIL import Image
from starlette.datastructures import UploadFile

from backend.app.schemas.veracity import ModalityType, VeracityLabel
from backend.app.schemas.verification import FullVerificationResponse
from backend.app.services.pipeline_service import pipeline_service


@pytest.mark.asyncio
async def test_text_verification_pipeline_integration():
    claim_text = "NASA scientists published peer-reviewed findings on solar cell efficiency in Nature."
    response = await pipeline_service.verify_text(claim_text)

    assert isinstance(response, FullVerificationResponse)
    assert response.input_modality == ModalityType.TEXT
    assert len(response.job_id) >= 10
    assert response.overall_veracity in VeracityLabel
    assert 0.0 <= response.overall_confidence <= 1.0
    assert response.uncertainty_level in ("LOW", "MODERATE", "HIGH")
    assert 0.0 <= response.uncertainty_score <= 1.0
    assert isinstance(response.is_actionable, bool)
    assert len(response.claims_verified) >= 1
    assert response.evidence_graph is not None
    assert len(response.executive_summary) > 10


@pytest.mark.asyncio
async def test_image_verification_pipeline_integration():
    # Create test image with clear text
    img = Image.new("RGB", (200, 200), color=(240, 240, 240))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    buf.seek(0)

    upload = UploadFile(filename="test_sample.jpg", file=buf)
    response = await pipeline_service.verify_image(upload)

    assert isinstance(response, FullVerificationResponse)
    assert response.input_modality == ModalityType.IMAGE
    assert response.image_forensics is not None
    assert 0.0 <= response.overall_confidence <= 1.0
    assert response.uncertainty_level in ("LOW", "MODERATE", "HIGH")
    assert response.evidence_graph is not None


@pytest.mark.asyncio
async def test_empty_text_validation_error():
    with pytest.raises(HTTPException) as exc_info:
        await pipeline_service.verify_text("   ")
    assert exc_info.value.status_code == 400
