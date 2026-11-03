"""Schemas for Payal Tool Registry and Function Calling."""

from enum import Enum, IntEnum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class PermissionLevel(IntEnum):
    """Operational permission tiers."""

    LEVEL_1_READ_ONLY = 1
    LEVEL_2_WORKSPACE_REVERSIBLE = 2
    LEVEL_3_APPROVAL_REQUIRED = 3
    LEVEL_4_RESTRICTED = 4


class ToolCategory(str, Enum):
    """Categorization of capabilities."""

    FILESYSTEM = "filesystem"
    TERMINAL = "terminal"
    BROWSER = "browser"
    GIT = "git"
    DATABASE = "database"
    SYSTEM = "system"
    CUSTOM = "custom"


class ToolDefinition(BaseModel):
    """Schema declaration and metadata of a registered tool."""

    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    category: ToolCategory
    permission_level: PermissionLevel
    parameters_schema: dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = False


class ToolCallRequest(BaseModel):
    """Structured invocation request emitted by the LLM or agent."""

    model_config = ConfigDict(extra="forbid")

    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    call_id: str | None = None


class ToolResult(BaseModel):
    """Standardized result returned by tool execution."""

    model_config = ConfigDict(extra="forbid")

    tool_name: str
    success: bool
    output: Any = None
    error: str | None = None
    call_id: str | None = None

