"""Cloud Model Providers (Groq & Gemini) for Payal."""

import os
import time
import httpx

from .base import ModelProvider
from .schemas import (
    CompletionRequest,
    CompletionResponse,
    ProviderHealth,
)


class GroqProvider(ModelProvider):
    name = "groq"
    base_url = "https://api.groq.com/openai/v1"

    def __init__(self, api_key: str | None = None, default_model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.default_model = default_model

    def _headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    async def list_models(self) -> list[str]:
        if not self.api_key:
            return []
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/models",
                headers=self._headers(),
            )
            response.raise_for_status()
            data = response.json()
        return [item["id"] for item in data.get("data", []) if isinstance(item, dict) and item.get("id")]

    async def health_check(self) -> ProviderHealth:
        if not self.api_key:
            return ProviderHealth(
                provider=self.name,
                available=False,
                error="GROQ_API_KEY environment variable is not set",
            )
        started = time.perf_counter()
        try:
            models = await self.list_models()
            return ProviderHealth(
                provider=self.name,
                available=True,
                latency_ms=round((time.perf_counter() - started) * 1000, 2),
                models=models,
            )
        except Exception as exc:
            return ProviderHealth(
                provider=self.name,
                available=False,
                latency_ms=round((time.perf_counter() - started) * 1000, 2),
                error=str(exc),
            )

    async def generate(self, request: CompletionRequest) -> CompletionResponse:
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is not configured.")

        model = request.model or self.default_model
        payload = {
            "model": model,
            "messages": [message.model_dump() for message in request.messages],
            "temperature": request.temperature,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens

        timeout = request.timeout_seconds or 60.0
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
            raise RuntimeError("Groq returned no completion choices.")
        content = choices[0].get("message", {}).get("content", "")

        return CompletionResponse(
            content=content,
            model=data.get("model", model),
            provider=self.name,
            session_id=request.session_id,
            usage=data.get("usage", {}),
        )


class GeminiProvider(ModelProvider):
    name = "gemini"
    base_url = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, api_key: str | None = None, default_model: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.default_model = default_model

    async def list_models(self) -> list[str]:
        if not self.api_key:
            return []
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/models?key={self.api_key}")
            response.raise_for_status()
            data = response.json()
        return [
            item["name"].replace("models/", "")
            for item in data.get("models", [])
            if "generateContent" in item.get("supportedGenerationMethods", [])
        ]

    async def health_check(self) -> ProviderHealth:
        if not self.api_key:
            return ProviderHealth(
                provider=self.name,
                available=False,
                error="GEMINI_API_KEY environment variable is not set",
            )
        started = time.perf_counter()
        try:
            models = await self.list_models()
            return ProviderHealth(
                provider=self.name,
                available=True,
                latency_ms=round((time.perf_counter() - started) * 1000, 2),
                models=models,
            )
        except Exception as exc:
            return ProviderHealth(
                provider=self.name,
                available=False,
                latency_ms=round((time.perf_counter() - started) * 1000, 2),
                error=str(exc),
            )

    async def generate(self, request: CompletionRequest) -> CompletionResponse:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")

        model = request.model or self.default_model
        # Format messages for Gemini generateContent
        contents = []
        for msg in request.messages:
            role = "user" if msg.role in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": msg.content}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
            },
        }
        if request.max_tokens is not None:
            payload["generationConfig"]["maxOutputTokens"] = request.max_tokens

        timeout = request.timeout_seconds or 60.0
        endpoint = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(endpoint, json=payload)
            response.raise_for_status()
            data = response.json()

        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini returned no candidates.")
        parts = candidates[0].get("content", {}).get("parts", [])
        content = parts[0].get("text", "") if parts else ""

        usage = data.get("usageMetadata", {})
        return CompletionResponse(
            content=content,
            model=model,
            provider=self.name,
            session_id=request.session_id,
            usage=usage,
        )

