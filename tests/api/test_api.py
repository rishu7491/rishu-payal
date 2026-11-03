"""Unit and integration tests for Payal Core API."""

import pytest
from fastapi.testclient import TestClient

from core.identity.persona import SYSTEM_PROMPT
from core.model_router.base import ModelProvider
from core.model_router.router import ModelRouter
from core.model_router.schemas import (
    ChatMessage,
    CompletionRequest,
    CompletionResponse,
    ProviderHealth,
)
from services.api.app import create_app
from services.api.routes.chat import get_model_router as chat_get_router
from services.api.routes.health import get_model_router as health_get_router
from services.api.routes.models import get_model_router as models_get_router


class MockProvider(ModelProvider):
    name = "mock_provider"

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.last_messages: list[ChatMessage] = []

    async def generate(self, request: CompletionRequest) -> CompletionResponse:
        self.last_messages = request.messages
        if self.should_fail:
            raise RuntimeError("Upstream provider connection error")
        return CompletionResponse(
            content="Mock response from Payal",
            model=request.model or "mock-model",
            provider=self.name,
            session_id=request.session_id,
        )

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider=self.name,
            available=not self.should_fail,
            latency_ms=15.0 if not self.should_fail else None,
            models=["mock-model-v1", "mock-model-v2"],
        )

    async def list_models(self) -> list[str]:
        if self.should_fail:
            raise RuntimeError("Failed to list models")
        return ["mock-model-v1", "mock-model-v2"]


@pytest.fixture
def test_setup():
    provider = MockProvider()
    router = ModelRouter(
        config=None,
        providers={"mock_provider": provider},
        primary_provider="mock_provider",
    )
    app = create_app()

    # Override dependencies
    app.dependency_overrides[chat_get_router] = lambda: router
    app.dependency_overrides[health_get_router] = lambda: router
    app.dependency_overrides[models_get_router] = lambda: router

    client = TestClient(app)
    return client, provider, router


def test_root_endpoint(test_setup):
    client, _, _ = test_setup
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["platform"] == "Payal"
    assert data["owner"] == "Rishu"
    assert data["status"] == "operational"
    assert data["version"] == "1.0.0"


def test_health_endpoints(test_setup):
    client, _, _ = test_setup
    for endpoint in ["/health", "/api/v1/health"]:
        res = client.get(endpoint)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["identity"]["name"] == "Payal"
        assert data["identity"]["owner"] == "Rishu"
        assert "mock_provider" in data["providers"]
        assert data["providers"]["mock_provider"]["available"] is True


def test_models_endpoint(test_setup):
    client, _, _ = test_setup
    res = client.get("/api/v1/models")
    assert res.status_code == 200
    data = res.json()
    assert data["primary_provider"] == "mock_provider"
    assert "mock_provider" in data["providers"]
    assert data["all_models"] == ["mock-model-v1", "mock-model-v2"]


def test_models_filter_endpoint(test_setup):
    client, _, _ = test_setup
    res = client.get("/api/v1/models?provider=mock_provider")
    assert res.status_code == 200
    data = res.json()
    assert data["providers"]["mock_provider"] == ["mock-model-v1", "mock-model-v2"]


def test_models_unknown_provider(test_setup):
    client, _, _ = test_setup
    res = client.get("/api/v1/models?provider=nonexistent")
    assert res.status_code == 400
    assert "Unknown provider" in res.json()["detail"]


def test_chat_success_with_system_prompt_injection(test_setup):
    client, provider, _ = test_setup
    payload = {
        "messages": [{"role": "user", "content": "Hello Payal"}],
        "model": "mock-model-v1",
        "temperature": 0.5,
    }
    res = client.post("/api/v1/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["content"] == "Mock response from Payal"
    assert data["provider"] == "mock_provider"
    assert data["model"] == "mock-model-v1"

    # Verify system prompt was injected
    assert len(provider.last_messages) == 2
    assert provider.last_messages[0].role == "system"
    assert provider.last_messages[0].content == SYSTEM_PROMPT
    assert provider.last_messages[1].role == "user"


def test_chat_custom_system_prompt_not_overridden(test_setup):
    client, provider, _ = test_setup
    custom_sys = "You are a custom assistant."
    payload = {
        "messages": [
            {"role": "system", "content": custom_sys},
            {"role": "user", "content": "Help me code."},
        ],
    }
    res = client.post("/api/v1/chat", json=payload)
    assert res.status_code == 200

    assert len(provider.last_messages) == 2
    assert provider.last_messages[0].content == custom_sys


def test_chat_empty_messages_validation(test_setup):
    client, _, _ = test_setup
    res = client.post("/api/v1/chat", json={"messages": []})
    assert res.status_code == 400
    assert "cannot be empty" in res.json()["detail"]


def test_chat_provider_failure_returns_502(test_setup):
    client, provider, _ = test_setup
    provider.should_fail = True
    payload = {
        "messages": [{"role": "user", "content": "Trigger failure"}],
    }
    res = client.post("/api/v1/chat", json=payload)
    assert res.status_code == 502
    assert "Upstream provider connection error" in res.json()["detail"]
