"""API Schemas for Payal Core Engine."""

from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from core.model_router.schemas import ChatMessage


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    messages: list[ChatMessage]
    model: str | None = None
    provider: str | None = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1)
    timeout_seconds: float | None = Field(default=None, gt=0, le=600)
    session_id: str | None = None
    include_system_prompt: bool = True


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str
    model: str
    provider: str
    session_id: str | None = None


class ModelsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    providers: dict[str, list[str]]
    all_models: list[str]
    primary_provider: str


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    version: str
    identity: dict[str, Any]
    providers: dict[str, Any]

