from pydantic import BaseModel, Field


class ImageForensicIndicators(BaseModel):
    has_exif: bool = Field(default=False, description="Whether EXIF metadata was present")
    software_tag: str | None = Field(default=None, description="Software tag detected in EXIF (e.g. Adobe Photoshop)")
    c2pa_present: bool = Field(default=False, description="Whether C2PA / Content Credentials manifest was found")
    ela_max_error: float = Field(default=0.0, ge=0.0, le=1.0, description="Normalized Error Level Analysis variance")
    is_ela_spliced: bool = Field(default=False, description="Indicator of localized compression inconsistency")
    synthetic_probability: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Continuous probabilistic estimate of AI generation (e.g. Midjourney/Flux/SD)"
    )
    synthetic_confidence: str = Field(
        default="LOW",
        description="Confidence category: LOW, MODERATE, HIGH (calibrated based on compression limits)"
    )
    forensic_notes: list[str] = Field(default_factory=list, description="Forensic observations and warnings")


class VideoForensicIndicators(BaseModel):
    duration_seconds: float = Field(default=0.0, ge=0.0)
    total_frames: int = Field(default=0, ge=0)
    extracted_scenes: int = Field(default=0, ge=0)
    has_audio_track: bool = Field(default=False)
    inconsistent_frame_rate: bool = Field(default=False)
    synthetic_face_probability: float | None = Field(default=None, ge=0.0, le=1.0)


class MultimodalExtractedContent(BaseModel):
    raw_text: str | None = None
    scraped_title: str | None = None
    scraped_body: str | None = None
    ocr_extracted_text: str | None = None
    asr_transcript: str | None = None
    image_forensics: ImageForensicIndicators | None = None
    video_forensics: VideoForensicIndicators | None = None
    combined_corpus: str = Field(..., description="Unified normalized textual corpus ready for claim extraction")
