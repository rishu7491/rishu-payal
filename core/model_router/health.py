"""Health monitoring service for Payal Model Providers."""

import asyncio
from .base import ModelProvider


class ProviderHealthMonitor:

    def __init__(self, providers: dict[str, ModelProvider]):
        self.providers = providers

    async def check_all(self) -> dict:
        names = list(self.providers.keys())
        results = await asyncio.gather(
            *(self.providers[name].health_check() for name in names),
            return_exceptions=True,
        )
        report = {}
        for name, result in zip(names, results):
            if isinstance(result, Exception):
                report[name] = {
                    "provider": name,
                    "available": False,
                    "error": str(result),
                }
            else:
                report[name] = result.model_dump()
        return report

