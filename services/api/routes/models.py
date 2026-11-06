"""Model listing endpoint for Payal Core Engine."""

from fastapi import APIRouter, Depends, HTTPException, Query
from core.identity.config import CONFIG
from core.model_router.router import ROUTER, ModelRouter
from services.api.schemas import ModelsResponse


router = APIRouter(prefix="/api/v1", tags=["Models"])


def get_model_router() -> ModelRouter:
    """Dependency for obtaining the shared ModelRouter singleton."""
    return ROUTER


@router.get("/models", response_model=ModelsResponse)
async def list_models(
    provider: str | None = Query(default=None, description="Optional provider filter"),
    router_instance: ModelRouter = Depends(get_model_router),
):
    """List available LLM models from configured providers."""
    try:
        if provider:
            models = await router_instance.list_models(provider)
            providers_dict = {provider: models}
            all_models = list(models)
        else:
            providers_dict = await router_instance.list_models()
            unique_models: set[str] = set()
            for m_list in providers_dict.values():
                unique_models.update(m_list)
            all_models = sorted(unique_models)

        return ModelsResponse(
            providers=providers_dict,
            all_models=all_models,
            primary_provider=router_instance.primary_provider,
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception as err:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to retrieve models from provider: {err}",
        )

