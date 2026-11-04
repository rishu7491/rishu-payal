"""Payal Execution Tools Package."""

from .base import BaseTool
from .builtin import (
    KaliTool,
    ListDirectoryTool,
    PowerShellTool,
    ReadFileTool,
    WriteFileTool,
)
from .ecc_tools import (
    CallECCAgentTool,
    GetECCRulesTool,
    RunECCCommandTool,
    RunECCSkillTool,
    SearchECCComponentsTool,
)
from .memory_tools import (
    DeleteMemoryTool,
    GetMemoryTool,
    SaveMemoryTool,
    SearchMemoryTool,
)
from .registry import ToolRegistry
from .schemas import (
    PermissionLevel,
    ToolCallRequest,
    ToolCategory,
    ToolDefinition,
    ToolResult,
)


def create_default_tool_registry() -> ToolRegistry:
    """Create a ToolRegistry loaded with all built-in and ECC tools."""
    registry = ToolRegistry()
    registry.register(ReadFileTool())
    registry.register(ListDirectoryTool())
    registry.register(WriteFileTool())
    registry.register(PowerShellTool())
    registry.register(KaliTool())
    registry.register(CallECCAgentTool())
    registry.register(RunECCSkillTool())
    registry.register(GetECCRulesTool())
    registry.register(RunECCCommandTool())
    registry.register(SearchECCComponentsTool())
    registry.register(SearchMemoryTool())
    registry.register(SaveMemoryTool())
    registry.register(GetMemoryTool())
    registry.register(DeleteMemoryTool())
    return registry


# Global default tool registry
DEFAULT_TOOL_REGISTRY = create_default_tool_registry()

__all__ = [
    "BaseTool",
    "ToolRegistry",
    "DEFAULT_TOOL_REGISTRY",
    "create_default_tool_registry",
    "PermissionLevel",
    "ToolCategory",
    "ToolDefinition",
    "ToolCallRequest",
    "ToolResult",
    "ReadFileTool",
    "ListDirectoryTool",
    "WriteFileTool",
    "PowerShellTool",
    "KaliTool",
    "CallECCAgentTool",
    "RunECCSkillTool",
    "GetECCRulesTool",
    "RunECCCommandTool",
    "SearchECCComponentsTool",
    "SearchMemoryTool",
    "SaveMemoryTool",
    "GetMemoryTool",
    "DeleteMemoryTool",
]
