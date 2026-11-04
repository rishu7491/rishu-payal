"""Tests for Payal Memory & Knowledge System (Phase 4)."""

import os
from pathlib import Path
import tempfile
import pytest

from core.memory.context_manager import ContextManager
from core.memory.models import MemoryItem, MemoryKind, MemoryScope, MemoryStatus
from core.memory.retriever import MemoryRetriever
from core.memory.storage import PersistentMemoryStore
from core.memory.manager import MemoryManager


@pytest.fixture
def temp_store(tmp_path):
    """Provides a fresh temporary SQLite memory store."""
    db_file = tmp_path / "test_memory.db"
    return PersistentMemoryStore(db_path=db_file)


@pytest.fixture
def temp_memory_manager(temp_store):
    """Provides a fresh MemoryManager backed by the temporary store."""
    ctx = ContextManager(max_tokens_estimate=1000)
    retriever = MemoryRetriever(store=temp_store)
    return MemoryManager(store=temp_store, context=ctx, retriever=retriever)


def test_memory_storage_crud(temp_store):
    """Verify create, read, update, delete operations on PersistentMemoryStore."""
    item = MemoryItem(
        title="Test API Guideline",
        content="Always use standard HTTP status codes.",
        kind=MemoryKind.FACT,
        scope=MemoryScope.PROJECT,
        tags=["api", "rest"],
        importance=0.8,
    )

    # 1. Save
    saved = temp_store.save(item)
    assert saved.id == item.id

    # 2. Get
    fetched = temp_store.get(item.id)
    assert fetched is not None
    assert fetched.title == "Test API Guideline"
    assert fetched.content == "Always use standard HTTP status codes."
    assert "api" in fetched.tags

    # 3. Update
    updated = temp_store.update(item.id, {"importance": 0.95, "title": "Updated Guideline"})
    assert updated is not None
    assert updated.importance == 0.95
    assert updated.title == "Updated Guideline"

    # 4. Delete
    deleted = temp_store.delete(item.id)
    assert deleted is True
    assert temp_store.get(item.id) is None


def test_memory_secret_sanitization(temp_store):
    """Verify that credentials and tokens are redacted before persistence."""
    leaky_content = "Connect using token: 'ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890' for authentication."
    item = MemoryItem(
        title="Token config",
        content=leaky_content,
        kind=MemoryKind.PREFERENCE,
    )
    saved = temp_store.save(item)
    assert "ghp_" not in saved.content
    assert "[REDACTED_SECRET]" in saved.content


def test_memory_search_and_ranking(temp_store):
    """Verify token overlap and keyword search ranking."""
    item1 = MemoryItem(
        title="PostgreSQL Indexing",
        content="Use B-tree indexes for high cardinality columns in Postgres.",
        kind=MemoryKind.KNOWLEDGE,
        tags=["database", "postgres", "sql"],
        importance=0.9,
    )
    item2 = MemoryItem(
        title="Frontend CSS Colors",
        content="Use Realtime Colors 60-30-10 palette distribution.",
        kind=MemoryKind.KNOWLEDGE,
        tags=["ui", "css", "colors"],
        importance=0.5,
    )
    temp_store.save(item1)
    temp_store.save(item2)

    results = temp_store.search("postgres database indexing", limit=5)
    assert len(results) >= 1
    assert results[0].title == "PostgreSQL Indexing"


def test_context_manager_tiers():
    """Verify Harness tiered context management (L0, L1, L2)."""
    ctx = ContextManager(max_tokens_estimate=500)
    ctx.set_l0(goal="Build authentication module", constraints=["No plaintext passwords", "WCAG AA"])
    ctx.set_l1(architecture="FastAPI + JWT + Bcrypt", components=["agency-backend-architect"])
    ctx.append_l2("TOOL_CALL", "Generated hash function in auth/hash.py")

    built = ctx.build_context()
    assert "[L0 - Abstract Goal & Constraints]" in built
    assert "Build authentication module" in built
    assert "[L1 - Architecture & Overview]" in built
    assert "FastAPI + JWT + Bcrypt" in built
    assert "[L2 - Active Execution Details]" in built
    assert "TOOL_CALL" in built


def test_memory_manager_workflow(temp_memory_manager):
    """Verify full MemoryManager lifecycle: recall, record task, conversation."""
    mgr = temp_memory_manager

    # Save knowledge
    mgr.save_knowledge(
        title="Payment Gateway Timeout",
        content="Set payment gateway request timeout to 30s.",
        tags=["payments", "stripe"],
    )

    # Prepare task context (Retrieval step)
    context_str = mgr.prepare_task_context(goal="Refactor payment gateway stripe calls")
    assert "Payment Gateway Timeout" in context_str

    # Record Task Completion
    task_mem = mgr.record_task_completion(
        goal="Refactor payment gateway stripe calls",
        summary="Updated timeout to 30 seconds and added retry loop.",
        components_used=["agency-backend-architect", "powershell_exec"],
        outcome="All unit tests passed.",
        success=True,
    )
    assert task_mem.kind == MemoryKind.TASK_SUMMARY
    assert "stripe" in task_mem.tags

    # Record Conversation
    chat_mem = mgr.record_conversation(
        user_message="How do we handle payments?",
        assistant_response="We use 30s timeouts with Stripe.",
    )
    assert chat_mem.kind == MemoryKind.CONVERSATION

    stats = mgr.get_stats()
    assert stats["total_memories"] >= 3

