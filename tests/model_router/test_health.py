import pytest
from core.model_router.health import ProviderHealthMonitor
from core.model_router.schemas import ProviderHealth


class HealthyProvider:
    name = "test"

    async def health_check(self):
        return ProviderHealth(
            provider="test",
            available=True,
            latency_ms=12.5,
            models=["model-a", "model-b"],
        )


class FailingProvider:
    name = "failing"

    async def health_check(self):
        raise RuntimeError("Connection refused")


@pytest.mark.anyio
async def test_health_monitor_success():
    monitor = ProviderHealthMonitor({"test": HealthyProvider()})
    result = await monitor.check_all()

    assert result["test"]["available"] is True
    assert result["test"]["latency_ms"] == 12.5
    assert result["test"]["models"] == ["model-a", "model-b"]


@pytest.mark.anyio
async def test_health_monitor_exception_handling():
    monitor = ProviderHealthMonitor({
        "healthy": HealthyProvider(),
        "broken": FailingProvider(),
    })
    result = await monitor.check_all()

    assert result["healthy"]["available"] is True
    assert result["broken"]["available"] is False
    assert "Connection refused" in result["broken"]["error"]

