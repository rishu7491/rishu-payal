"""Health check endpoint for Payal Core Engine."""

from fastapi import APIRouter, Depends
from core.identity.config import CONFIG, PayalConfig
from core.identity.identity import get_identity
from core.model_router.router import ModelRouter
from services.api.schemas import HealthResponse


router = APIRouter(tags=["Health"])


def get_model_router() -> ModelRouter:
    """Dependency for obtaining the ModelRouter instance."""
    return ModelRouter(config=CONFIG)


@router.get("/health", response_model=HealthResponse)
@router.get("/api/health", response_model=HealthResponse)
@router.get("/api/v1/health", response_model=HealthResponse)
async def health_check(
    router_instance: ModelRouter = Depends(get_model_router),
):
    """Return platform status, Payal identity, and provider health states."""
    identity = get_identity()
    providers_health = await router_instance.health_monitor.check_all()

    return HealthResponse(
        status="ok",
        version=CONFIG.config_version,
        identity={
            "name": identity.name,
            "owner": identity.owner,
            "title": identity.title,
            "languages": identity.languages,
        },
        providers=providers_health,
    )

