import pytest
from core.model_router.base import ModelProvider
from core.model_router.router import ModelRouter
from core.model_router.schemas import (
    ChatMessage,
    CompletionRequest,
    CompletionResponse,
    ProviderHealth,
)


class FakeProvider(ModelProvider):
    def __init__(self, name: str, should_fail: bool = False, models: list[str] = None):
        self.name = name
        self.should_fail = should_fail
        self.calls = 0
        self.models_list = models or ["test-model-1", "test-model-2"]

    async def generate(self, request: CompletionRequest) -> CompletionResponse:
        self.calls += 1
        if self.should_fail:
            raise RuntimeError(f"Simulated failure in provider '{self.name}'")
        return CompletionResponse(
            content=f"Response from {self.name}",
            model=request.model or "test-model-1",
            provider=self.name,
            session_id=request.session_id,
        )

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider=self.name,
            available=not self.should_fail,
            latency_ms=10.0 if not self.should_fail else None,
            error="Failed" if self.should_fail else None,
            models=self.models_list if not self.should_fail else [],
        )

    async def list_models(self) -> list[str]:
        if self.should_fail:
            raise RuntimeError(f"Cannot list models from {self.name}")
        return self.models_list


@pytest.mark.anyio
async def test_router_generate_primary_success():
    provider_a = FakeProvider("primary_prov")
    router = ModelRouter(config=None, providers={"primary_prov": provider_a}, primary_provider="primary_prov")

    req = CompletionRequest(
        messages=[ChatMessage(role="user", content="Hello")]
    )
    res = await router.generate(req)

    assert res.content == "Response from primary_prov"
    assert res.provider == "primary_prov"
    assert provider_a.calls == 1


@pytest.mark.anyio
async def test_router_fallback_on_failure():
    primary = FakeProvider("primary_prov", should_fail=True)
    fallback = FakeProvider("fallback_prov", should_fail=False)

    router = ModelRouter(
        config=None,
        providers={"primary_prov": primary, "fallback_prov": fallback},
        primary_provider="primary_prov",
    )

    req = CompletionRequest(
        messages=[ChatMessage(role="user", content="Hello")]
    )
    res = await router.generate(req, fallback_providers=["fallback_prov"])

    assert res.content == "Response from fallback_prov"
    assert res.provider == "fallback_prov"
    assert primary.calls == 1
    assert fallback.calls == 1


@pytest.mark.anyio
async def test_router_all_fail_raises():
    primary = FakeProvider("primary_prov", should_fail=True)
    fallback = FakeProvider("fallback_prov", should_fail=True)

    router = ModelRouter(
        config=None,
        providers={"primary_prov": primary, "fallback_prov": fallback},
        primary_provider="primary_prov",
    )

    req = CompletionRequest(
        messages=[ChatMessage(role="user", content="Hello")]
    )

    with pytest.raises(RuntimeError) as exc_info:
        await router.generate(req, fallback_providers=["fallback_prov"])

    assert "Model generation failed across all attempted providers" in str(exc_info.value)


@pytest.mark.anyio
async def test_router_unknown_provider_raises():
    router = ModelRouter(config=None, providers={"prov_a": FakeProvider("prov_a")})
    req = CompletionRequest(messages=[ChatMessage(role="user", content="Hi")])

    with pytest.raises(ValueError) as exc_info:
        await router.generate(req, provider_name="non_existent")

    assert "is not registered" in str(exc_info.value)


@pytest.mark.anyio
async def test_router_list_models_all_and_specific():
    prov_a = FakeProvider("prov_a", models=["m-1", "m-2"])
    prov_b = FakeProvider("prov_b", models=["m-3"])

    router = ModelRouter(config=None, providers={"prov_a": prov_a, "prov_b": prov_b})

    # Specific provider
    models_a = await router.list_models("prov_a")
    assert models_a == ["m-1", "m-2"]

    # All providers
    all_models = await router.list_models()
    assert all_models["prov_a"] == ["m-1", "m-2"]
    assert all_models["prov_b"] == ["m-3"]

