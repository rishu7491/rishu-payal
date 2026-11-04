"""SQLite Persistent Storage Engine for Payal Memory System."""

import json
import os
from pathlib import Path
import re
import sqlite3
import time
from typing import Any, Dict, List, Optional

from .models import MemoryItem, MemoryKind, MemoryScope, MemoryStatus

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "memory" / "payal_memory.db"

# Secret hygiene patterns to prevent credential leaks into durable memory
SECRET_PATTERNS = [
    re.compile(r"(?i)(bearer|token|apikey|api_key|password|secret|private_key)\s*[:=]\s*['\"][A-Za-z0-9_\-\.]{16,}['\"]"),
    re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
]


class PersistentMemoryStore:
    """Manages SQLite-backed persistent memory records with secret filtering and search."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.has_category_column = False
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Create or migrate tables and search indexes."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    kind TEXT NOT NULL DEFAULT 'knowledge',
                    scope TEXT NOT NULL DEFAULT 'project',
                    status TEXT NOT NULL DEFAULT 'active',
                    uri TEXT,
                    tags TEXT NOT NULL DEFAULT '[]',
                    metadata TEXT NOT NULL DEFAULT '{}',
                    importance REAL DEFAULT 0.5,
                    access_count INTEGER DEFAULT 0,
                    created_at REAL NOT NULL DEFAULT 0.0,
                    updated_at REAL NOT NULL DEFAULT 0.0
                )
                """
            )
            # Migrate any missing columns if table existed with an older schema
            columns = [info[1] for info in conn.execute("PRAGMA table_info(memories)").fetchall()]
            if "category" in columns:
                self.has_category_column = True
            if "kind" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN kind TEXT DEFAULT 'knowledge'")
                if "category" in columns:
                    conn.execute("UPDATE memories SET kind = category WHERE kind = 'knowledge'")
            if "scope" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN scope TEXT DEFAULT 'project'")
            if "status" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN status TEXT DEFAULT 'active'")
            if "uri" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN uri TEXT")

            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_kind ON memories(kind)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_scope ON memories(scope)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_status ON memories(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_uri ON memories(uri)")
            conn.commit()

    def _sanitize_content(self, text: str) -> str:
        """Redact detected credentials to maintain secret hygiene."""
        sanitized = text
        for pat in SECRET_PATTERNS:
            sanitized = pat.sub("[REDACTED_SECRET]", sanitized)
        return sanitized

    def save(self, item: MemoryItem) -> MemoryItem:
        """Insert or update a memory item in SQLite."""
        clean_content = self._sanitize_content(item.content)
        clean_title = self._sanitize_content(item.title)
        tags_json = json.dumps(item.tags)
        meta_json = json.dumps(item.metadata)
        now = time.time()
        kind_val = item.kind.value if isinstance(item.kind, MemoryKind) else str(item.kind)
        scope_val = item.scope.value if isinstance(item.scope, MemoryScope) else str(item.scope)
        status_val = item.status.value if isinstance(item.status, MemoryStatus) else str(item.status)

        with self._get_connection() as conn:
            if self.has_category_column:
                conn.execute(
                    """
                    INSERT INTO memories (
                        id, title, content, kind, category, scope, status, uri, tags, metadata,
                        importance, access_count, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        title=excluded.title,
                        content=excluded.content,
                        kind=excluded.kind,
                        category=excluded.category,
                        scope=excluded.scope,
                        status=excluded.status,
                        uri=excluded.uri,
                        tags=excluded.tags,
                        metadata=excluded.metadata,
                        importance=excluded.importance,
                        updated_at=excluded.updated_at
                    """,
                    (
                        item.id,
                        clean_title,
                        clean_content,
                        kind_val,
                        kind_val,  # category mirror
                        scope_val,
                        status_val,
                        item.uri,
                        tags_json,
                        meta_json,
                        item.importance,
                        item.access_count,
                        item.created_at or now,
                        now,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO memories (
                        id, title, content, kind, scope, status, uri, tags, metadata,
                        importance, access_count, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        title=excluded.title,
                        content=excluded.content,
                        kind=excluded.kind,
                        scope=excluded.scope,
                        status=excluded.status,
                        uri=excluded.uri,
                        tags=excluded.tags,
                        metadata=excluded.metadata,
                        importance=excluded.importance,
                        updated_at=excluded.updated_at
                    """,
                    (
                        item.id,
                        clean_title,
                        clean_content,
                        kind_val,
                        scope_val,
                        status_val,
                        item.uri,
                        tags_json,
                        meta_json,
                        item.importance,
                        item.access_count,
                        item.created_at or now,
                        now,
                    ),
                )
            conn.commit()

        item.content = clean_content
        item.title = clean_title
        item.updated_at = now
        return item

    def get(self, memory_id: str) -> Optional[MemoryItem]:
        """Fetch memory item by ID."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
            if not row:
                return None
            return self._row_to_item(row)

    def update(self, memory_id: str, updates: Dict[str, Any]) -> Optional[MemoryItem]:
        """Update selected fields of an existing memory item."""
        item = self.get(memory_id)
        if not item:
            return None

        if "title" in updates:
            item.title = updates["title"]
        if "content" in updates:
            item.content = updates["content"]
        if "kind" in updates:
            item.kind = updates["kind"]
        if "scope" in updates:
            item.scope = updates["scope"]
        if "status" in updates:
            item.status = updates["status"]
        if "uri" in updates:
            item.uri = updates["uri"]
        if "tags" in updates:
            item.tags = updates["tags"]
        if "metadata" in updates:
            item.metadata.update(updates["metadata"])
        if "importance" in updates:
            item.importance = float(updates["importance"])

        return self.save(item)

    def delete(self, memory_id: str) -> bool:
        """Delete a memory item by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            conn.commit()
            return cursor.rowcount > 0

    def count(self) -> int:
        """Return total count of stored memory records."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM memories").fetchone()
            return row[0] if row else 0

    def list(
        self,
        kind: Optional[str] = None,
        scope: Optional[str] = None,
        status: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 50,
    ) -> List[MemoryItem]:
        """List memory items with optional filters."""
        query = "SELECT * FROM memories WHERE 1=1"
        params: List[Any] = []

        if kind:
            query += " AND kind = ?"
            params.append(kind)
        if scope:
            query += " AND scope = ?"
            params.append(scope)
        if status:
            query += " AND status = ?"
            params.append(status)
        if tag:
            query += " AND tags LIKE ?"
            params.append(f"%{tag}%")

        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_item(r) for r in rows]

    def search(
        self,
        query: str,
        limit: int = 10,
        min_importance: float = 0.0,
    ) -> List[MemoryItem]:
        """Keyword and token-overlap search across title, content, uri, and tags."""
        terms = [t.lower() for t in re.findall(r"\b\w+\b", query) if len(t) > 2]
        if not terms:
            return self.list(limit=limit)

        sql = "SELECT * FROM memories WHERE status = 'active' AND importance >= ?"
        with self._get_connection() as conn:
            rows = conn.execute(sql, (min_importance,)).fetchall()

        scored: List[tuple[float, MemoryItem]] = []
        for r in rows:
            item = self._row_to_item(r)
            score = 0.0
            text_corpus = f"{item.title} {item.content} {item.uri or ''} {' '.join(item.tags)}".lower()

            # Exact query match boost
            if query.lower() in text_corpus:
                score += 10.0

            # Token matches
            for term in terms:
                if term in item.title.lower():
                    score += 5.0
                if term in (item.uri or "").lower():
                    score += 4.0
                if any(term in tag.lower() for tag in item.tags):
                    score += 3.0
                if term in item.content.lower():
                    score += 1.0

            # Weight by importance
            score = score * (1.0 + item.importance)

            if score > 0:
                scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:limit]]

    def record_access(self, memory_id: str) -> None:
        """Increment access count and touch updated timestamp."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE memories SET access_count = access_count + 1 WHERE id = ?",
                (memory_id,),
            )
            conn.commit()

    def get_stats(self) -> Dict[str, Any]:
        """Aggregate counts by kind and scope."""
        with self._get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            by_kind = dict(
                conn.execute("SELECT kind, COUNT(*) FROM memories GROUP BY kind").fetchall()
            )
            by_scope = dict(
                conn.execute("SELECT scope, COUNT(*) FROM memories GROUP BY scope").fetchall()
            )
        return {
            "total_memories": total,
            "by_kind": by_kind,
            "by_scope": by_scope,
            "db_path": str(self.db_path),
        }

    def _row_to_item(self, row: sqlite3.Row) -> MemoryItem:
        tags = []
        try:
            tags = json.loads(row["tags"])
        except Exception:
            pass

        metadata = {}
        try:
            metadata = json.loads(row["metadata"])
        except Exception:
            pass

        return MemoryItem(
            id=row["id"],
            title=row["title"],
            content=row["content"],
            kind=MemoryKind(row["kind"]) if row["kind"] in MemoryKind._value2member_map_ else MemoryKind.KNOWLEDGE,
            scope=MemoryScope(row["scope"]) if row["scope"] in MemoryScope._value2member_map_ else MemoryScope.PROJECT,
            status=MemoryStatus(row["status"]) if row["status"] in MemoryStatus._value2member_map_ else MemoryStatus.ACTIVE,
            uri=row["uri"],
            tags=tags,
            metadata=metadata,
            importance=row["importance"],
            access_count=row["access_count"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


# Global singleton persistent store
PERSISTENT_MEMORY_STORE = PersistentMemoryStore()
