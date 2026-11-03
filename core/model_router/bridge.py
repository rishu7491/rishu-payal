"""AGY Local API Bridge Provider for Payal."""

import time
import httpx

from .base import ModelProvider
from .schemas import (
    CompletionRequest,
    CompletionResponse,
    ProviderHealth,
)


class AGYBridgeProvider(ModelProvider):
    name = "agy_bridge"

    def __init__(self, config):
        self.config = config
        model_cfg = getattr(config, "model", config)
        self.base_url = getattr(
            model_cfg, "agy_bridge_url", "http://127.0.0.1:8788/v1"
        ).rstrip("/")
        self.api_key = getattr(model_cfg, "api_key", "local")
        self.default_model = getattr(
            model_cfg, "agy_model", "gemini-3.8-flash-high"
        )
        self.default_timeout = getattr(model_cfg, "timeout_seconds", 120)

    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def list_models(self) -> list[str]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{self.base_url}/models",
                headers=self._headers(),
            )
            response.raise_for_status()
            data = response.json()

        return [
            item["id"]
            for item in data.get("data", [])
            if isinstance(item, dict) and item.get("id")
        ]

    async def health_check(self) -> ProviderHealth:
        started = time.perf_counter()

        try:
            models = await self.list_models()
            return ProviderHealth(
                provider=self.name,
                available=True,
                latency_ms=round(
                    (time.perf_counter() - started) * 1000, 2
                ),
                models=models,
            )
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            return ProviderHealth(
                provider=self.name,
                available=False,
                latency_ms=round(
                    (time.perf_counter() - started) * 1000, 2
                ),
                error=str(exc),
            )

    async def generate(
        self, request: CompletionRequest
    ) -> CompletionResponse:
        model = request.model or self.default_model

        payload = {
            "model": model,
            "messages": [
                message.model_dump() for message in request.messages
            ],
            "temperature": request.temperature,
        }

        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens

        if request.session_id:
            payload["session_id"] = request.session_id

        timeout = (
            request.timeout_seconds
            or float(self.default_timeout)
        )

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self._headers(),
            )
            response.raise_for_status()
            data = response.json()

        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("Bridge returned no completion choices.")

        content = choices[0].get("message", {}).get("content")
        if not isinstance(content, str):
            raise RuntimeError("Bridge returned an invalid message.")

        return CompletionResponse(
            content=content,
            model=data.get("model", model),
            provider=self.name,
            session_id=data.get("session_id", request.session_id),
            usage=data.get("usage", {}),
        )

