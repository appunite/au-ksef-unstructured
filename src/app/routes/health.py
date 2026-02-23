from fastapi import APIRouter

from src.app.schemas.extract import HealthResponse

router = APIRouter(tags=["System"])


@router.get(
    "/health",
    summary="Health check",
    description="Returns service health status. Use for liveness/readiness probes.",
    response_model=HealthResponse,
)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")
