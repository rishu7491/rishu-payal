import pytest
from core.model_router.bridge import AGYBridgeProvider
from core.model_router.schemas import CompletionRequest, ChatMessage


class DummyConfig:
    agy_bridge_url = "http://127.0.0.1:8788/v1"
    agy_model = "gemini-3.8-flash-high"
    api_key = "test_key"
    timeout_seconds = 60


def test_bridge_initialization_and_headers():
    cfg = DummyConfig()
    provider = AGYBridgeProvider(cfg)

    assert provider.name == "agy_bridge"
    assert provider.base_url == "http://127.0.0.1:8788/v1"
    headers = provider._headers()
    assert headers["Authorization"] == "Bearer test_key"
    assert headers["Content-Type"] == "application/json"


def test_bridge_empty_api_key_headers():
    cfg = DummyConfig()
    cfg.api_key = ""
    provider = AGYBridgeProvider(cfg)
    headers = provider._headers()
    assert "Authorization" not in headers

