from fastapi import APIRouter
from backend.app.schemas.verification import FullVerificationResponse
from backend.app.core.config import settings

api_router = APIRouter()


@api_router.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }
