"""Tool Registry for Payal Core Engine."""

from typing import Any
from .base import BaseTool
from .schemas import (
    PermissionLevel,
    ToolCategory,
    ToolCallRequest,
    ToolDefinition,
)


class ToolRegistry:
    """Central registry and schema catalog for all operational tools."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        if not tool.name or not isinstance(tool.name, str):
            raise ValueError("Tool name must be a non-empty string.")

        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered.")

        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        """Unregister a tool by name."""
        if name in self._tools:
            del self._tools[name]

    def get(self, name: str) -> BaseTool | None:
        """Retrieve a registered tool instance by name."""
        return self._tools.get(name)

    def has_tool(self, name: str) -> bool:
        """Check if a tool exists in the registry."""
        return name in self._tools

    def list_tools(
        self,
        category: ToolCategory | None = None,
        max_permission: PermissionLevel | None = None,
    ) -> list[BaseTool]:
        """List registered tools with optional category and permission level filter."""
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        if max_permission is not None:
            tools = [t for t in tools if t.permission_level <= max_permission]
        return tools

    def get_definitions(
        self,
        category: ToolCategory | None = None,
        max_permission: PermissionLevel | None = None,
    ) -> list[ToolDefinition]:
        """Return standardized definitions for tools."""
        tools = self.list_tools(category=category, max_permission=max_permission)
        return [tool.get_definition() for tool in tools]

    def export_openai_tools(
        self,
        category: ToolCategory | None = None,
        max_permission: PermissionLevel | None = None,
    ) -> list[dict[str, Any]]:
        """Export tool definitions in OpenAI/LLM function calling format."""
        definitions = self.get_definitions(
            category=category, max_permission=max_permission
        )
        tools_payload: list[dict[str, Any]] = []

        for d in definitions:
            tools_payload.append({
                "type": "function",
                "function": {
                    "name": d.name,
                    "description": d.description,
                    "parameters": d.parameters_schema or {
                        "type": "object",
                        "properties": {},
                    },
                },
            })

        return tools_payload

    def validate_call(self, request: ToolCallRequest) -> tuple[bool, str | None]:
        """Validate a tool call request against registry schemas without executing.

        Returns (is_valid, error_message).
        """
        tool = self.get(request.tool_name)
        if not tool:
            return False, f"Tool '{request.tool_name}' is not registered."

        try:
            tool.validate_arguments(request.arguments)
            return True, None
        except ValueError as err:
            return False, str(err)

