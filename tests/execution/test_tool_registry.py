"""Unit tests for Payal Tool Registry and Schemas (Phase 2A)."""

import pytest
from pydantic import BaseModel, Field

from execution.tools import (
    BaseTool,
    KaliTool,
    ListDirectoryTool,
    PermissionLevel,
    PowerShellTool,
    ReadFileTool,
    ToolCallRequest,
    ToolCategory,
    ToolRegistry,
    WriteFileTool,
)


class CustomArgs(BaseModel):
    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, ge=1, le=100)


class CustomSearchTool(BaseTool):
    name = "custom_search"
    description = "Perform a search query."
    category = ToolCategory.CUSTOM
    permission_level = PermissionLevel.LEVEL_1_READ_ONLY
    args_schema = CustomArgs


def test_tool_registration_and_retrieval():
    registry = ToolRegistry()
    tool = ReadFileTool()

    assert not registry.has_tool("read_file")
    registry.register(tool)

    assert registry.has_tool("read_file")
    assert registry.get("read_file") is tool
    assert len(registry.list_tools()) == 1


def test_duplicate_registration_raises():
    registry = ToolRegistry()
    registry.register(ReadFileTool())

    with pytest.raises(ValueError, match="already registered"):
        registry.register(ReadFileTool())


def test_unregister_tool():
    registry = ToolRegistry()
    registry.register(ReadFileTool())
    assert registry.has_tool("read_file")

    registry.unregister("read_file")
    assert not registry.has_tool("read_file")
    assert registry.get("read_file") is None


def test_tool_definition_generation():
    tool = WriteFileTool()
    defn = tool.get_definition()

    assert defn.name == "write_file"
    assert defn.category == ToolCategory.FILESYSTEM
    assert defn.permission_level == PermissionLevel.LEVEL_2_WORKSPACE_REVERSIBLE
    assert defn.requires_approval is False
    assert defn.parameters_schema["type"] == "object"
    assert "path" in defn.parameters_schema["properties"]
    assert "content" in defn.parameters_schema["properties"]
    assert "path" in defn.parameters_schema["required"]
    assert "content" in defn.parameters_schema["required"]


def test_level_3_tool_requires_approval():
    ps_tool = PowerShellTool()
    defn = ps_tool.get_definition()
    assert defn.permission_level == PermissionLevel.LEVEL_3_APPROVAL_REQUIRED
    assert defn.requires_approval is True

    kali_tool = KaliTool()
    k_defn = kali_tool.get_definition()
    assert k_defn.permission_level == PermissionLevel.LEVEL_3_APPROVAL_REQUIRED
    assert k_defn.requires_approval is True


def test_permission_level_filtering():
    registry = ToolRegistry()
    registry.register(ReadFileTool())       # Level 1
    registry.register(ListDirectoryTool())  # Level 1
    registry.register(WriteFileTool())      # Level 2
    registry.register(PowerShellTool())     # Level 3
    registry.register(KaliTool())           # Level 3

    # Only Level 1
    l1_tools = registry.list_tools(max_permission=PermissionLevel.LEVEL_1_READ_ONLY)
    assert len(l1_tools) == 2
    assert {t.name for t in l1_tools} == {"read_file", "list_directory"}

    # Level 1 and 2
    l2_tools = registry.list_tools(max_permission=PermissionLevel.LEVEL_2_WORKSPACE_REVERSIBLE)
    assert len(l2_tools) == 3
    assert {t.name for t in l2_tools} == {"read_file", "list_directory", "write_file"}

    # All up to Level 3
    l3_tools = registry.list_tools(max_permission=PermissionLevel.LEVEL_3_APPROVAL_REQUIRED)
    assert len(l3_tools) == 5


def test_category_filtering():
    registry = ToolRegistry()
    registry.register(ReadFileTool())
    registry.register(PowerShellTool())
    registry.register(CustomSearchTool())

    fs_tools = registry.list_tools(category=ToolCategory.FILESYSTEM)
    assert len(fs_tools) == 1
    assert fs_tools[0].name == "read_file"

    term_tools = registry.list_tools(category=ToolCategory.TERMINAL)
    assert len(term_tools) == 1
    assert term_tools[0].name == "powershell_exec"


def test_export_openai_tools():
    registry = ToolRegistry()
    registry.register(ReadFileTool())
    registry.register(WriteFileTool())

    exported = registry.export_openai_tools()
    assert len(exported) == 2

    first = exported[0]
    assert first["type"] == "function"
    assert first["function"]["name"] == "read_file"
    assert "parameters" in first["function"]
    assert "path" in first["function"]["parameters"]["properties"]


def test_argument_validation_success():
    registry = ToolRegistry()
    registry.register(CustomSearchTool())

    req = ToolCallRequest(
        tool_name="custom_search",
        arguments={"query": "python async", "limit": 25},
    )
    is_valid, err = registry.validate_call(req)
    assert is_valid is True
    assert err is None


def test_argument_validation_missing_required_field():
    registry = ToolRegistry()
    registry.register(CustomSearchTool())

    # 'query' is required but omitted
    req = ToolCallRequest(
        tool_name="custom_search",
        arguments={"limit": 25},
    )
    is_valid, err = registry.validate_call(req)
    assert is_valid is False
    assert "Field required" in err


def test_argument_validation_unknown_tool():
    registry = ToolRegistry()
    req = ToolCallRequest(tool_name="nonexistent", arguments={})
    is_valid, err = registry.validate_call(req)
    assert is_valid is False
    assert "is not registered" in err


@pytest.mark.anyio
async def test_tool_execution_strictly_disabled_in_phase_2a():
    tool = ReadFileTool()
    with pytest.raises(NotImplementedError) as exc_info:
        await tool.execute({"path": "sample.txt"})

    assert "disabled in Phase 2A" in str(exc_info.value)
    assert "activated in Phase 2C" in str(exc_info.value)

