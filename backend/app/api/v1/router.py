from fastapi import APIRouter
from backend.app.api.v1.endpoints.ingest import router as ingest_router
from backend.app.api.v1.endpoints.jobs import router as jobs_router
from backend.app.api.v1.endpoints.baseline import router as baseline_router
from backend.app.api.v1.endpoints.claims import router as claims_router
from backend.app.api.v1.endpoints.verify import router as verify_router
from backend.app.core.config import settings

api_router = APIRouter()

# Mount feature routers
api_router.include_router(ingest_router)
api_router.include_router(jobs_router)
api_router.include_router(baseline_router)
api_router.include_router(claims_router)
api_router.include_router(verify_router)


@api_router.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }
