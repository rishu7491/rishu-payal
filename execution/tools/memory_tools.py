"""Memory Tools for Payal Tool Registry.

Allows LLM and autonomous agents to search, retrieve, save, and manage
long-term memories, user preferences, and knowledge artifacts.
"""

from typing import Any, List, Optional
from pydantic import BaseModel, Field

from .base import BaseTool
from .schemas import PermissionLevel, ToolCategory, ToolResult
from core.memory import MEMORY_MANAGER, MemoryManager, MemoryKind, MemoryScope


class SearchMemoryArgs(BaseModel):
    query: str = Field(..., description="Query terms to search memory and knowledge items")
    limit: int = Field(default=5, description="Maximum number of memory items to return")


class SearchMemoryTool(BaseTool):
    name = "search_memory"
    description = "Search long-term memory for past conversations, tasks, lessons, and knowledge."
    category = ToolCategory.CUSTOM
    permission_level = PermissionLevel.LEVEL_1_READ_ONLY
    args_schema = SearchMemoryArgs

    def __init__(self, manager: Optional[MemoryManager] = None):
        super().__init__()
        self.manager = manager or MEMORY_MANAGER

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        args = SearchMemoryArgs(**arguments)
        items = self.manager.search_memories(query=args.query, limit=args.limit)
        results = [
            {
                "id": it.id,
                "title": it.title,
                "kind": it.kind.value,
                "scope": it.scope.value,
                "uri": it.uri,
                "tags": it.tags,
                "content": it.content[:500],
            }
            for it in items
        ]
        return ToolResult(
            tool_name=self.name,
            success=True,
            output=str(results),
            metadata={"count": len(results)},
        )


class SaveMemoryArgs(BaseModel):
    title: str = Field(..., description="Title or headline of the memory item")
    content: str = Field(..., description="Content of the memory or knowledge item")
    kind: str = Field(default="knowledge", description="Kind: 'knowledge', 'lesson', 'preference', 'fact', or 'decision'")
    tags: List[str] = Field(default_factory=list, description="Keywords or tags for categorization")
    uri: Optional[str] = Field(default=None, description="Optional OpenViking URI, e.g. viking://~/preferences/...")


class SaveMemoryTool(BaseTool):
    name = "save_memory"
    description = "Persist durable knowledge, lessons, or user preferences into long-term memory."
    category = ToolCategory.CUSTOM
    permission_level = PermissionLevel.LEVEL_2_WORKSPACE_REVERSIBLE
    args_schema = SaveMemoryArgs

    def __init__(self, manager: Optional[MemoryManager] = None):
        super().__init__()
        self.manager = manager or MEMORY_MANAGER

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        args = SaveMemoryArgs(**arguments)
        kind_enum = MemoryKind(args.kind) if args.kind in MemoryKind._value2member_map_ else MemoryKind.KNOWLEDGE
        item = self.manager.save_knowledge(
            title=args.title,
            content=args.content,
            tags=args.tags,
            uri=args.uri,
        )
        if kind_enum != MemoryKind.KNOWLEDGE:
            self.manager.update_memory(item.id, {"kind": kind_enum.value})

        return ToolResult(
            tool_name=self.name,
            success=True,
            output=f"Memory saved successfully with ID: {item.id}",
            metadata={"id": item.id, "uri": item.uri},
        )


class GetMemoryArgs(BaseModel):
    memory_id: str = Field(..., description="Unique ID of the memory item to retrieve")


class GetMemoryTool(BaseTool):
    name = "get_memory"
    description = "Retrieve the full content and metadata of a specific memory item by ID."
    category = ToolCategory.CUSTOM
    permission_level = PermissionLevel.LEVEL_1_READ_ONLY
    args_schema = GetMemoryArgs

    def __init__(self, manager: Optional[MemoryManager] = None):
        super().__init__()
        self.manager = manager or MEMORY_MANAGER

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        args = GetMemoryArgs(**arguments)
        item = self.manager.get_memory(args.memory_id)
        if not item:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=f"Memory item '{args.memory_id}' not found.",
            )
        return ToolResult(
            tool_name=self.name,
            success=True,
            output=item.model_dump_json(),
            metadata={"id": item.id, "kind": item.kind.value},
        )


class DeleteMemoryArgs(BaseModel):
    memory_id: str = Field(..., description="ID of the memory item to delete")


class DeleteMemoryTool(BaseTool):
    name = "delete_memory"
    description = "Remove a memory item from persistent storage (requires approval for sensitive data)."
    category = ToolCategory.CUSTOM
    permission_level = PermissionLevel.LEVEL_3_APPROVAL_REQUIRED
    args_schema = DeleteMemoryArgs

    def __init__(self, manager: Optional[MemoryManager] = None):
        super().__init__()
        self.manager = manager or MEMORY_MANAGER

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        args = DeleteMemoryArgs(**arguments)
        deleted = self.manager.delete_memory(args.memory_id)
        return ToolResult(
            tool_name=self.name,
            success=deleted,
            output=f"Memory item '{args.memory_id}' {'deleted' if deleted else 'not found'}.",
            error=None if deleted else "Item not found",
        )
