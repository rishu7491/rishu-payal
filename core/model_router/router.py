"""Central Model Router for Payal AI."""

from typing import Dict, List, Optional
from core.identity.config import CONFIG
from .base import ModelProvider
from .bridge import AGYBridgeProvider
from .llama_cpp import LlamaCppProvider
from .cloud import GroqProvider, GeminiProvider
from .health import ProviderHealthMonitor
from .schemas import CompletionRequest, CompletionResponse


class ModelRouter:

    def __init__(
        self,
        config=None,
        providers: Optional[Dict[str, ModelProvider]] = None,
        primary_provider: Optional[str] = None,
    ):
        self.config = config or CONFIG
        model_cfg = getattr(self.config, "model", self.config)
        self.primary_provider = primary_provider or getattr(
            model_cfg, "primary_provider", "agy_bridge"
        )

        if providers is not None:
            self.providers = providers
        else:
            self.providers = {
                "agy_bridge": AGYBridgeProvider(self.config),
                "llamacpp": LlamaCppProvider(self.config),
                "groq": GroqProvider(),
                "gemini": GeminiProvider(),
            }

        self.health_monitor = ProviderHealthMonitor(self.providers)

    async def check_health(self) -> dict:
        return await self.health_monitor.check_all()

    async def list_models(self, provider_name: Optional[str] = None) -> dict | list:
        if provider_name:
            provider = self.providers.get(provider_name)
            if provider is None:
                raise ValueError(f"Unknown provider: {provider_name}")
            return await provider.list_models()

        results = {}
        for name, provider in self.providers.items():
            try:
                results[name] = await provider.list_models()
            except Exception as exc:
                results[name] = []
        return results

    async def generate(
        self,
        request: CompletionRequest,
        provider_name: Optional[str] = None,
        fallback_providers: Optional[List[str]] = None,
    ) -> CompletionResponse:
        target_name = provider_name or self.primary_provider
        provider = self.providers.get(target_name)

        if provider is None:
            raise ValueError(f"Target provider '{target_name}' is not registered.")

        attempts = [target_name] + (fallback_providers or [])
        last_error = None

        for name in attempts:
            current_provider = self.providers.get(name)
            if current_provider is None:
                continue
            try:
                return await current_provider.generate(request)
            except Exception as exc:
                last_error = exc

        raise RuntimeError(
            f"Model generation failed across all attempted providers ({', '.join(attempts)}). "
            f"Last error: {last_error}"
        )


# Shared default router instance
ROUTER = ModelRouter(CONFIG)
