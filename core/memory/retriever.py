"""Memory Retrieval Engine for Payal Memory & Knowledge System.

Performs ranked semantic & keyword retrieval over persistent memory
and OpenViking URIs (viking://~/ and viking://agent/).
"""

from typing import List, Optional

from .models import MemoryItem, MemoryKind, MemoryScope
from .storage import PERSISTENT_MEMORY_STORE, PersistentMemoryStore


class MemoryRetriever:
    """Retrieves relevant historical memories, user preferences, and knowledge items."""

    def __init__(self, store: Optional[PersistentMemoryStore] = None):
        self.store = store or PERSISTENT_MEMORY_STORE

    def retrieve(
        self,
        query: str,
        limit: int = 5,
        min_importance: float = 0.2,
        preferred_scope: Optional[MemoryScope] = None,
    ) -> List[MemoryItem]:
        """Find the most relevant memory artifacts for the given query."""
        results = self.store.search(
            query=query,
            limit=limit * 2,
            min_importance=min_importance,
        )

        if preferred_scope:
            # Boost items matching preferred scope
            results.sort(
                key=lambda x: (x.scope == preferred_scope, x.importance, x.updated_at),
                reverse=True,
            )

        final_items = results[:limit]

        # Record access to update retrieval analytics
        for item in final_items:
            self.store.record_access(item.id)

        return final_items

    def recall_preferences(self, limit: int = 5) -> List[MemoryItem]:
        """Recall saved user preferences and operational directives."""
        return self.store.list(kind=MemoryKind.PREFERENCE.value, limit=limit)

    def recall_lessons(self, topic: Optional[str] = None, limit: int = 5) -> List[MemoryItem]:
        """Recall past lessons and failure post-mortems."""
        if topic:
            items = self.store.search(query=topic, limit=limit)
            return [it for it in items if it.kind == MemoryKind.LESSON]
        return self.store.list(kind=MemoryKind.LESSON.value, limit=limit)


# Global singleton retriever
MEMORY_RETRIEVER = MemoryRetriever()

