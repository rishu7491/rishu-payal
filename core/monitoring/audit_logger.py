"""Audit Logger for Payal AI.

Maintains an immutable, append-only ledger of sensitive actions, tool calls,
approvals, and security events for full observability and compliance.
"""

from dataclasses import dataclass, asdict
import hashlib
import json
import os
import time
from typing import Any, Dict, List, Optional
from core.identity.config import CONFIG


@dataclass
class AuditEntry:
    entry_id: str
    timestamp: float
    iso_time: str
    event_type: str  # e.g., "tool_execution", "approval", "security_alert", "system_task"
    actor: str       # e.g., "payal_orchestrator", "user", "background_worker"
    action: str
    target: str
    status: str      # "SUCCESS", "FAILED", "BLOCKED", "PENDING"
    details: Dict[str, Any]
    checksum: str = ""

    def calculate_checksum(self) -> str:
        payload = f"{self.entry_id}:{self.timestamp}:{self.event_type}:{self.actor}:{self.action}:{self.target}:{self.status}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


class AuditLogger:
    """Manages append-only persistent audit trail."""

    def __init__(self, log_path: Optional[str] = None):
        base_dir = getattr(getattr(CONFIG, "storage", None), "base_dir", "data")
        self.log_path = log_path or os.path.join(base_dir, "audit_ledger.jsonl")
        os.makedirs(os.path.dirname(os.path.abspath(self.log_path)), exist_ok=True)
        self._cache: List[AuditEntry] = []
        self._load_cache()

    def _load_cache(self, max_recent: int = 100) -> None:
        if not os.path.exists(self.log_path):
            return
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-max_recent:]:
                    if line.strip():
                        data = json.loads(line)
                        entry = AuditEntry(**data)
                        self._cache.append(entry)
        except Exception:
            pass

    def log(
        self,
        event_type: str,
        action: str,
        target: str,
        actor: str = "payal_orchestrator",
        status: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        """Record an immutable audit entry."""
        now = time.time()
        iso = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(now))
        entry_id = f"aud-{int(now * 1000)}"

        entry = AuditEntry(
            entry_id=entry_id,
            timestamp=now,
            iso_time=iso,
            event_type=event_type,
            actor=actor,
            action=action,
            target=target,
            status=status,
            details=details or {},
        )
        entry.checksum = entry.calculate_checksum()

        # Append to persistent ledger
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(entry)) + "\n")
        except Exception:
            pass

        self._cache.append(entry)
        if len(self._cache) > 200:
            self._cache.pop(0)

        return entry

    def query(
        self,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Query audit log entries with optional filtering."""
        results = []
        # Read from file or cache
        entries = self._cache
        for item in reversed(entries):
            if event_type and item.event_type != event_type:
                continue
            if status and item.status != status.upper():
                continue
            results.append(asdict(item))
            if len(results) >= limit:
                break
        return results


AUDIT_LOGGER = AuditLogger()
