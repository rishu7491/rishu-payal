"""Abstract base class for all Payal Model Providers."""

from abc import ABC, abstractmethod

from .schemas import (
    CompletionRequest,
    CompletionResponse,
    ProviderHealth,
)


class ModelProvider(ABC):
    name: str

    @abstractmethod
    async def generate(
        self, request: CompletionRequest
    ) -> CompletionResponse:
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> ProviderHealth:
        raise NotImplementedError

    @abstractmethod
    async def list_models(self) -> list[str]:
        raise NotImplementedError

