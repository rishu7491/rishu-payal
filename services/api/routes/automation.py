"""API routes for Payal Proactive Intelligence & Background Automation Engine."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.automation import (
    BACKGROUND_TASK_MANAGER,
    NOTIFICATION_HUB,
    PROACTIVE_ENGINE,
    TASK_SCHEDULER,
    ScheduleType,
    TaskStatus,
)

router = APIRouter(prefix="/api/automation", tags=["Automation & Proactive"])


class SubmitTaskRequest(BaseModel):
    name: str = Field(..., description="Task title")
    goal: str = Field(..., description="Goal to execute in background")
    context: Optional[str] = None
    auto_approve_safe: bool = True


class CreateScheduleRequest(BaseModel):
    name: str = Field(..., description="Schedule title")
    goal: str = Field(..., description="Goal to run periodically")
    schedule_type: str = Field(default="interval", description="'interval', 'once', or 'cron'")
    interval_seconds: float = Field(default=3600.0, ge=1.0)
    delay_seconds: float = Field(default=0.0, ge=0.0)
    cron_expr: Optional[str] = None


@router.get("/tasks")
async def list_background_tasks(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
):
    """List running and historical background tasks."""
    st = TaskStatus(status) if status in TaskStatus._value2member_map_ else None
    tasks = BACKGROUND_TASK_MANAGER.list_tasks(status=st, limit=limit)
    return [t.model_dump() for t in tasks]


@router.post("/tasks")
async def submit_background_task(req: SubmitTaskRequest):
    """Submit a task for asynchronous background execution."""
    task = BACKGROUND_TASK_MANAGER.submit_task(
        name=req.name,
        goal=req.goal,
        context=req.context,
        auto_approve_safe=req.auto_approve_safe,
    )
    return task.model_dump()


@router.get("/tasks/{task_id}")
async def get_task_details(task_id: str):
    """Get status, progress, logs, and output of a background task."""
    task = BACKGROUND_TASK_MANAGER.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return task.model_dump()


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel an in-progress background task."""
    cancelled = BACKGROUND_TASK_MANAGER.cancel_task(task_id)
    if not cancelled:
        raise HTTPException(status_code=400, detail=f"Cannot cancel task '{task_id}' (not running or not found).")
    return {"status": "cancelled", "task_id": task_id}


@router.get("/schedules")
async def list_schedules(active_only: bool = False):
    """List scheduled jobs."""
    jobs = TASK_SCHEDULER.list_jobs(active_only=active_only)
    return [j.model_dump() for j in jobs]


@router.post("/schedules")
async def create_schedule(req: CreateScheduleRequest):
    """Create a recurring or delayed scheduled job."""
    st_type = ScheduleType(req.schedule_type) if req.schedule_type in ScheduleType._value2member_map_ else ScheduleType.INTERVAL
    job = TASK_SCHEDULER.add_job(
        name=req.name,
        goal=req.goal,
        schedule_type=st_type,
        interval_seconds=req.interval_seconds,
        delay_seconds=req.delay_seconds,
        cron_expr=req.cron_expr,
    )
    return job.model_dump()


@router.delete("/schedules/{job_id}")
async def delete_schedule(job_id: str):
    """Remove a scheduled job."""
    deleted = TASK_SCHEDULER.remove_job(job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Schedule '{job_id}' not found.")
    return {"status": "deleted", "job_id": job_id}


@router.get("/suggestions")
async def list_proactive_suggestions(status: Optional[str] = None):
    """List proactive ideas, optimizations, and project opportunities."""
    sugs = PROACTIVE_ENGINE.list_suggestions(status=status)
    return [s.model_dump() for s in sugs]


@router.post("/proactive/scan")
async def trigger_proactive_scan(auto_execute_safe: bool = False):
    """Trigger the full loop: Observe → Research → Think → Plan → Notify."""
    suggestions = await PROACTIVE_ENGINE.run_cycle(auto_execute_safe=auto_execute_safe)
    return [s.model_dump() for s in suggestions]


@router.post("/suggestions/{sug_id}/accept")
async def accept_suggestion(sug_id: str):
    """Accept and launch execution for a proactive suggestion."""
    accepted = PROACTIVE_ENGINE.accept_suggestion(sug_id)
    if not accepted:
        raise HTTPException(status_code=404, detail=f"Suggestion '{sug_id}' not found.")
    return accepted.model_dump()


@router.get("/notifications")
async def list_notifications(unread_only: bool = False, limit: int = 50):
    """Fetch notifications and system alerts."""
    notifs = NOTIFICATION_HUB.list_notifications(unread_only=unread_only, limit=limit)
    return {
        "unread_count": NOTIFICATION_HUB.get_unread_count(),
        "notifications": [n.model_dump() for n in notifs],
    }


@router.post("/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: str):
    """Mark notification as read."""
    marked = NOTIFICATION_HUB.mark_as_read(notif_id)
    if not marked:
        raise HTTPException(status_code=404, detail=f"Notification '{notif_id}' not found.")
    return {"status": "read", "id": notif_id}

