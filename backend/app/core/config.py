from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Multimodal Evidence-Aware Misinformation Verification System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Base paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOADS_DIR: Path = BASE_DIR / "uploads"
    
    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/verification.sqlite3"
    
    # Ingestion constraints
    MAX_TEXT_LENGTH: int = 20_000
    MAX_IMAGE_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB
    MAX_VIDEO_SIZE_BYTES: int = 60 * 1024 * 1024  # 60 MB
    MAX_VIDEO_DURATION_SECONDS: int = 90
    
    # External APIs (Optional - fallbacks are local)
    GOOGLE_FACTCHECK_API_KEY: str | None = None
    TAVILY_API_KEY: str | None = None
    
    # Verification Thresholds
    CHECKWORTHY_THRESHOLD: float = 0.60
    EVIDENCE_SUFFICIENCY_THRESHOLD: float = 1.20
    STANCE_SUPPORT_THRESHOLD: float = 0.70
    STANCE_REFUTE_THRESHOLD: float = 0.65
    TEMPORAL_OUTDATED_DAYS: int = 180
    SYNTHETIC_INDICATOR_THRESHOLD: float = 0.75
    
    # Model Caching
    CACHE_EXPIRATION_HOURS: int = 24
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

# Ensure required run-time directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
