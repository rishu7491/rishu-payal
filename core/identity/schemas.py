"""Validated schemas for Payal identity and configuration."""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class IdentitySchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = "Payal"
    owner: str = "Rishu"
    title: str = "Independent AI Development Platform"
    languages: list[str] = Field(
        default_factory=lambda: ["Hindi", "English", "Hinglish"]
    )


class PersonaSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tone: str = "Calm, precise, warm and direct"
    style: str = "JARVIS-inspired"
    concise_by_default: bool = True
    verify_before_claiming_success: bool = True


class SecuritySchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default_permission_level: Literal[1, 2, 3, 4] = 1
    require_approval_for_kali: bool = True
    require_approval_for_external_actions: bool = True


class AppSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    environment: Literal["development", "testing", "production"] = "development"
    debug: bool = False

