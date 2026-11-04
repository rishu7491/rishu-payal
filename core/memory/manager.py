"""Central Memory Manager for Payal Core Engine.

Unifies Persistent SQLite Storage, Harness Tiered Context Management,
and Autonomous Memory Retrieval into a single cohesive interface.
"""

import re
import time
from typing import Any, Dict, List, Optional

from .context_manager import CONTEXT_MANAGER, ContextManager
from .models import MemoryItem, MemoryKind, MemoryScope, MemoryStatus
from .retriever import MEMORY_RETRIEVER, MemoryRetriever
from .storage import PERSISTENT_MEMORY_STORE, PersistentMemoryStore


class MemoryManager:
    """Coordinates persistent memory, contextual hierarchy, and retrieval."""

    def __init__(
        self,
        store: Optional[PersistentMemoryStore] = None,
        context: Optional[ContextManager] = None,
        retriever: Optional[MemoryRetriever] = None,
    ):
        self.store = store or PERSISTENT_MEMORY_STORE
        self.context = context or CONTEXT_MANAGER
        self.retriever = retriever or MEMORY_RETRIEVER

    def prepare_task_context(
        self,
        goal: str,
        base_context: Optional[str] = None,
        constraints: Optional[List[str]] = None,
    ) -> str:
        """Execute Memory Retrieval and populate Tiered Context (L0, L1, L2)."""
        self.context.clear()

        # 1. Retrieve relevant memories for the goal
        relevant_memories = self.retriever.retrieve(query=goal, limit=4)

        # 2. Build L0 (Abstract Goal & Constraints)
        self.context.set_l0(goal=goal, constraints=constraints)

        # 3. Build L1 (Overview & Recalled Memories)
        recalled_snippets: List[str] = []
        for mem in relevant_memories:
            recalled_snippets.append(f"[{mem.kind.value.upper()}: {mem.title}] {mem.content[:250]}")

        memories_summary = "\n".join(recalled_snippets) if recalled_snippets else "None recalled."
        overview_text = f"Relevant Historical Memory:\n{memories_summary}"
        if base_context:
            overview_text = f"{base_context}\n\n{overview_text}"

        self.context.set_l1(architecture=overview_text)

        return self.context.build_context()

    def record_task_completion(
        self,
        goal: str,
        summary: str,
        components_used: List[str],
        outcome: str,
        success: bool = True,
    ) -> MemoryItem:
        """Durable persistence of a completed task into Long-term Memory."""
        kind = MemoryKind.TASK_SUMMARY if success else MemoryKind.LESSON
        scope = MemoryScope.PROJECT
        title = f"{'Task Completed' if success else 'Task Failed'}: {goal[:60]}"
        content = (
            f"**Goal:** {goal}\n"
            f"**Status:** {'SUCCESS' if success else 'FAILED'}\n"
            f"**Components:** {', '.join(components_used)}\n"
            f"**Summary:** {summary}\n"
            f"**Outcome:** {outcome}"
        )

        goal_tags = [w.lower() for w in re.findall(r"\b\w+\b", goal) if len(w) > 3]
        component_tags = [c.lower() for c in components_used[:3]]
        all_tags = list(dict.fromkeys(["task-run", "orchestrator"] + component_tags + goal_tags[:4]))

        item = MemoryItem(
            title=title,
            content=content,
            kind=kind,
            scope=scope,
            status=MemoryStatus.ACTIVE,
            uri=f"viking://agent/tasks/{int(time.time())}",
            tags=all_tags,
            importance=0.8 if not success else 0.6,
            metadata={"goal": goal, "success": success, "components": components_used},
        )
        return self.store.save(item)

    def record_conversation(
        self,
        user_message: str,
        assistant_response: str,
        session_id: Optional[str] = None,
    ) -> MemoryItem:
        """Store conversational interaction for long-term multi-turn recall."""
        title = f"Conversation: {user_message[:50]}..."
        content = f"User: {user_message}\nPayal: {assistant_response}"
        item = MemoryItem(
            title=title,
            content=content,
            kind=MemoryKind.CONVERSATION,
            scope=MemoryScope.USER,
            status=MemoryStatus.ACTIVE,
            uri=f"viking://~/conversations/{session_id or 'default'}",
            tags=["conversation", "chat"],
            importance=0.4,
            metadata={"session_id": session_id},
        )
        return self.store.save(item)

    def save_knowledge(
        self,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        uri: Optional[str] = None,
        importance: float = 0.6,
    ) -> MemoryItem:
        """Store reference knowledge, facts, or technical documentation."""
        item = MemoryItem(
            title=title,
            content=content,
            kind=MemoryKind.KNOWLEDGE,
            scope=MemoryScope.PROJECT,
            status=MemoryStatus.ACTIVE,
            uri=uri or f"viking://agent/knowledge/{int(time.time())}",
            tags=tags or ["knowledge"],
            importance=importance,
        )
        return self.store.save(item)

    # --- Direct CRUD Control Interface for User ---

    def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        return self.store.get(memory_id)

    def list_memories(
        self,
        kind: Optional[str] = None,
        scope: Optional[str] = None,
        status: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 50,
    ) -> List[MemoryItem]:
        return self.store.list(kind=kind, scope=scope, status=status, tag=tag, limit=limit)

    def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> Optional[MemoryItem]:
        return self.store.update(memory_id, updates)

    def delete_memory(self, memory_id: str) -> bool:
        return self.store.delete(memory_id)

    def search_memories(self, query: str, limit: int = 10) -> List[MemoryItem]:
        return self.retriever.retrieve(query, limit=limit)

    def get_stats(self) -> Dict[str, Any]:
        return self.store.get_stats()


# Global singleton memory manager
MEMORY_MANAGER = MemoryManager()
