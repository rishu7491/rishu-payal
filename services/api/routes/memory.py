"""API routes for Memory & Knowledge System Control (CRUD, search, context inspection)."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.memory import MEMORY_MANAGER, MemoryItem, MemoryKind, MemoryScope

router = APIRouter(prefix="/api/memory", tags=["Memory & Knowledge"])


class CreateMemoryRequest(BaseModel):
    title: str = Field(..., description="Title of the memory artifact")
    content: str = Field(..., description="Text content")
    kind: str = Field(default="knowledge", description="Memory kind (conversation, task_summary, decision, lesson, preference, fact, knowledge)")
    scope: str = Field(default="project", description="Memory scope (user, project, system)")
    uri: Optional[str] = Field(default=None, description="OpenViking URI (e.g. viking://~/preferences/...)")
    tags: List[str] = Field(default_factory=list, description="Categorization tags")
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UpdateMemoryRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    kind: Optional[str] = None
    scope: Optional[str] = None
    status: Optional[str] = None
    uri: Optional[str] = None
    tags: Optional[List[str]] = None
    importance: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class SearchMemoryRequest(BaseModel):
    query: str = Field(..., description="Search query string")
    limit: int = Field(default=10, ge=1, le=50)


@router.get("/stats")
async def get_memory_stats():
    """Get aggregated statistics about stored memories."""
    return MEMORY_MANAGER.get_stats()


@router.get("/context")
async def get_active_context():
    """Inspect current active Harness tiered context (L0, L1, L2)."""
    return {
        "l0_abstract": MEMORY_MANAGER.context.tiers.l0_abstract,
        "l1_overview": MEMORY_MANAGER.context.tiers.l1_overview,
        "l2_detail": MEMORY_MANAGER.context.tiers.l2_detail,
        "assembled_prompt": MEMORY_MANAGER.context.build_context(),
    }


@router.get("")
async def list_memories(
    kind: Optional[str] = Query(None),
    scope: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
):
    """List memory items with optional filtering."""
    items = MEMORY_MANAGER.list_memories(kind=kind, scope=scope, status=status, tag=tag, limit=limit)
    return [it.model_dump() for it in items]


@router.get("/{memory_id}")
async def get_memory_by_id(memory_id: str):
    """Retrieve full details of a specific memory item."""
    item = MEMORY_MANAGER.get_memory(memory_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found.")
    return item.model_dump()


@router.post("")
async def create_memory(req: CreateMemoryRequest):
    """Store a new memory item."""
    kind_enum = MemoryKind(req.kind) if req.kind in MemoryKind._value2member_map_ else MemoryKind.KNOWLEDGE
    scope_enum = MemoryScope(req.scope) if req.scope in MemoryScope._value2member_map_ else MemoryScope.PROJECT

    item = MemoryItem(
        title=req.title,
        content=req.content,
        kind=kind_enum,
        scope=scope_enum,
        uri=req.uri,
        tags=req.tags,
        importance=req.importance,
        metadata=req.metadata,
    )
    saved = MEMORY_MANAGER.store.save(item)
    return saved.model_dump()


@router.put("/{memory_id}")
async def update_memory_by_id(memory_id: str, req: UpdateMemoryRequest):
    """Update fields on an existing memory item."""
    updates = req.model_dump(exclude_unset=True)
    updated = MEMORY_MANAGER.update_memory(memory_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found.")
    return updated.model_dump()


@router.delete("/{memory_id}")
async def delete_memory_by_id(memory_id: str):
    """Delete a memory item from persistent storage."""
    deleted = MEMORY_MANAGER.delete_memory(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found.")
    return {"status": "deleted", "memory_id": memory_id}


@router.post("/search")
async def search_memories(req: SearchMemoryRequest):
    """Search memories by keyword and semantic tokens."""
    results = MEMORY_MANAGER.search_memories(query=req.query, limit=req.limit)
    return [r.model_dump() for r in results]
