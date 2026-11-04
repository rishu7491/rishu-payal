"""Pydantic data models for Payal Proactive Intelligence & Automation Engine."""

from enum import Enum
import time
from typing import Any, Callable, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BackgroundTask(BaseModel):
    """An asynchronous long-running task running in background."""
    task_id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    name: str
    goal: str
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0  # 0.0 to 1.0
    logs: List[str] = Field(default_factory=list)
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScheduleType(str, Enum):
    INTERVAL = "interval"
    ONCE = "once"
    CRON = "cron"


class ScheduledJob(BaseModel):
    """A scheduled recurring or delayed execution job."""
    job_id: str = Field(default_factory=lambda: f"job_{uuid.uuid4().hex[:8]}")
    name: str
    goal: str
    schedule_type: ScheduleType = ScheduleType.INTERVAL
    interval_seconds: float = 3600.0  # Default 1 hour
    cron_expr: Optional[str] = None
    last_run: Optional[float] = None
    next_run: float = Field(default_factory=time.time)
    is_active: bool = True
    run_count: int = 0
    created_at: float = Field(default_factory=time.time)


class SuggestionPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ProactiveSuggestion(BaseModel):
    """An independently generated idea, improvement, or opportunity."""
    id: str = Field(default_factory=lambda: f"sug_{uuid.uuid4().hex[:8]}")
    title: str
    description: str
    rationale: str
    impact: str
    priority: SuggestionPriority = SuggestionPriority.MEDIUM
    action_goal: str
    category: str = "improvement"  # improvement, security, feature, performance
    status: str = "new"  # new, accepted, dismissed
    created_at: float = Field(default_factory=time.time)


class NotificationSeverity(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    CRITICAL = "critical"


class Notification(BaseModel):
    """An alert or notification delivered to user / desktop companion."""
    id: str = Field(default_factory=lambda: f"notif_{uuid.uuid4().hex[:8]}")
    type: str  # task_complete, task_failure, proactive_suggestion, security_alert
    title: str
    message: str
    severity: NotificationSeverity = NotificationSeverity.INFO
    timestamp: float = Field(default_factory=time.time)
    read: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

