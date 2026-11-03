"""Standardized schemas for Payal Model Router."""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["system", "user", "assistant", "tool"]
    content: str


class CompletionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    messages: list[ChatMessage]
    model: str | None = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1)
    timeout_seconds: float | None = Field(default=None, gt=0, le=600)
    session_id: str | None = None


class CompletionResponse(BaseModel):
    content: str
    model: str
    provider: str
    session_id: str | None = None
    usage: dict = Field(default_factory=dict)


class ProviderHealth(BaseModel):
    provider: str
    available: bool
    latency_ms: float | None = None
    error: str | None = None
    models: list[str] = Field(default_factory=list)

