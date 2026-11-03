"""Built-in tool declarations and schemas for Payal Core Engine.

Note: Execution is disabled in Phase 2A. These classes define schemas,
categories, and permission levels for policy evaluation.
"""

from pydantic import BaseModel, Field

from .base import BaseTool
from .schemas import PermissionLevel, ToolCategory


class ReadFileArgs(BaseModel):
    path: str = Field(..., description="Target file path to read")


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read text contents of a file within the project workspace."
    category = ToolCategory.FILESYSTEM
    permission_level = PermissionLevel.LEVEL_1_READ_ONLY
    args_schema = ReadFileArgs


class ListDirectoryArgs(BaseModel):
    path: str = Field(default=".", description="Target directory path to inspect")


class ListDirectoryTool(BaseTool):
    name = "list_directory"
    description = "List entries and metadata inside a workspace directory."
    category = ToolCategory.FILESYSTEM
    permission_level = PermissionLevel.LEVEL_1_READ_ONLY
    args_schema = ListDirectoryArgs


class WriteFileArgs(BaseModel):
    path: str = Field(..., description="Target file path to create or modify")
    content: str = Field(..., description="Content to write into the file")


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Write or overwrite content into a file within the approved workspace."
    category = ToolCategory.FILESYSTEM
    permission_level = PermissionLevel.LEVEL_2_WORKSPACE_REVERSIBLE
    args_schema = WriteFileArgs


class PowerShellArgs(BaseModel):
    command: str = Field(..., description="PowerShell command string to execute")
    cwd: str | None = Field(default=None, description="Working directory for the command")


class PowerShellTool(BaseTool):
    name = "powershell_exec"
    description = "Execute a command in Windows PowerShell (requires approval)."
    category = ToolCategory.TERMINAL
    permission_level = PermissionLevel.LEVEL_3_APPROVAL_REQUIRED
    args_schema = PowerShellArgs


class KaliArgs(BaseModel):
    command: str = Field(..., description="Linux/Kali command string to execute")


class KaliTool(BaseTool):
    name = "kali_exec"
    description = "Execute a command in isolated WSL2/Kali Linux environment (requires approval)."
    category = ToolCategory.TERMINAL
    permission_level = PermissionLevel.LEVEL_3_APPROVAL_REQUIRED
    args_schema = KaliArgs

