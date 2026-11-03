"""Base Tool specification for Payal Core Engine."""

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, ValidationError

from .schemas import PermissionLevel, ToolCategory, ToolDefinition, ToolResult


class BaseTool(ABC):
    """Abstract interface for all Payal tools."""

    name: str
    description: str
    category: ToolCategory
    permission_level: PermissionLevel = PermissionLevel.LEVEL_1_READ_ONLY
    args_schema: type[BaseModel] | None = None
    requires_approval: bool | None = None

    def __init__(self):
        if self.requires_approval is None:
            self.requires_approval = (
                self.permission_level >= PermissionLevel.LEVEL_3_APPROVAL_REQUIRED
            )

    def get_definition(self) -> ToolDefinition:
        """Return standardized tool definition and parameter schema."""
        schema: dict[str, Any] = {}
        if self.args_schema:
            raw_schema = self.args_schema.model_json_schema()
            # Clean up metadata for clean LLM tool calling schema
            schema = {
                "type": "object",
                "properties": raw_schema.get("properties", {}),
                "required": raw_schema.get("required", []),
            }

        return ToolDefinition(
            name=self.name,
            description=self.description,
            category=self.category,
            permission_level=self.permission_level,
            parameters_schema=schema,
            requires_approval=bool(self.requires_approval),
        )

    def validate_arguments(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Validate raw arguments dictionary against args_schema if defined."""
        if not self.args_schema:
            return arguments

        try:
            parsed = self.args_schema.model_validate(arguments)
            return parsed.model_dump()
        except ValidationError as err:
            raise ValueError(f"Invalid arguments for tool '{self.name}': {err}")

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Execution entrypoint.

        Direct tool execution is disabled during Phase 2A/2B until Policy Engine
        and Approval Manager in Phase 2C are fully established.
        """
        raise NotImplementedError(
            f"Execution of tool '{self.name}' is disabled in Phase 2A. "
            "Execution Runtime will be activated in Phase 2C after Policy Engine verification."
        )

