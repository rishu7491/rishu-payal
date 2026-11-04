"""Pydantic data models for Payal Persistent Memory & Context Manager."""

from enum import Enum
import time
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class MemoryKind(str, Enum):
    CONVERSATION = "conversation"
    TASK_SUMMARY = "task_summary"
    DECISION = "decision"
    LESSON = "lesson"
    PREFERENCE = "preference"
    FACT = "fact"
    KNOWLEDGE = "knowledge"


class MemoryScope(str, Enum):
    USER = "user"
    PROJECT = "project"
    SYSTEM = "system"


class MemoryStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"


class MemoryItem(BaseModel):
    """A durable memory or knowledge artifact."""
    id: str = Field(default_factory=lambda: f"mem_{uuid.uuid4().hex[:10]}")
    title: str
    content: str
    kind: MemoryKind = MemoryKind.KNOWLEDGE
    scope: MemoryScope = MemoryScope.PROJECT
    status: MemoryStatus = MemoryStatus.ACTIVE
    uri: Optional[str] = None  # e.g., viking://~/preferences/... or viking://agent/...
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    importance: float = 0.5  # 0.0 (trivial) to 1.0 (critical)
    access_count: int = 0
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class ContextTiers(BaseModel):
    """Harness Engineering tiered context hierarchy (L0, L1, L2)."""
    l0_abstract: str = ""  # Milestone goals, constraints, agent identity
    l1_overview: str = ""  # Architecture, active components, API contracts
    l2_detail: str = ""    # Active traces, recent tool outputs, tests, errors
    updated_at: float = Field(default_factory=time.time)

