"""Background Task Execution Engine for Payal Automation."""

import asyncio
import time
from typing import Any, Callable, Dict, List, Optional

from core.orchestrator import UNIFIED_ORCHESTRATOR, UnifiedOrchestrator
from .models import BackgroundTask, NotificationSeverity, TaskStatus
from .notifications import NOTIFICATION_HUB, NotificationHub


class BackgroundTaskManager:
    """Coordinates non-blocking background tasks and orchestrator jobs."""

    def __init__(
        self,
        orchestrator: Optional[UnifiedOrchestrator] = None,
        notifications: Optional[NotificationHub] = None,
    ):
        self.orchestrator = orchestrator or UNIFIED_ORCHESTRATOR
        self.notifications = notifications or NOTIFICATION_HUB
        self._tasks: Dict[str, BackgroundTask] = {}
        self._async_handles: Dict[str, asyncio.Task] = {}
        self._seed_default_tasks()

    def _seed_default_tasks(self) -> None:
        """Seed initial real user goals so task hub operates with actual database items."""
        initial_goals = [
            ("Complete BCA Notes", "Summarize Semester 4 Operating Systems & Data Structures units", "BCA Study • High Priority", 0.0, False),
            ("Workout 2 Hours", "Track evening calisthenics & strength training progress", "Health • Daily Habit", 0.35, False),
            ("Update RishuMart", "Audit database schema and API contracts for RishuMart", "Project • In Progress", 0.0, False),
            ("Check Phone Battery", "Monitor connected device battery, memory, and telemetry", "Daily • System Monitor", 1.0, True),
        ]
        for name, goal, cat, prog, completed in initial_goals:
            t = BackgroundTask(
                name=name,
                goal=goal,
                status=TaskStatus.COMPLETED if completed else TaskStatus.RUNNING,
                progress=prog,
                metadata={"category": cat},
            )
            if completed:
                t.completed_at = time.time()
            self._tasks[t.task_id] = t

    def toggle_task(self, task_id: str, done: bool) -> Optional[BackgroundTask]:
        """Toggle task completion state."""
        task = self._tasks.get(task_id)
        if task:
            task.status = TaskStatus.COMPLETED if done else TaskStatus.RUNNING
            task.progress = 1.0 if done else 0.5
            if done:
                task.completed_at = time.time()
            return task
        return None

    def submit_task(
        self,
        name: str,
        goal: str,
        context: Optional[str] = None,
        auto_approve_safe: bool = True,
    ) -> BackgroundTask:
        """Submit a user goal for asynchronous background execution."""
        task = BackgroundTask(
            name=name,
            goal=goal,
            status=TaskStatus.PENDING,
            metadata={"context": context, "auto_approve_safe": auto_approve_safe},
        )
        self._tasks[task.task_id] = task

        async_handle = asyncio.create_task(
            self._execute_orchestrator_task(task, context, auto_approve_safe)
        )
        self._async_handles[task.task_id] = async_handle
        return task

    def submit_job(
        self,
        name: str,
        goal: str,
        coro_func: Callable[..., Any],
        *args,
        **kwargs,
    ) -> BackgroundTask:
        """Submit an arbitrary coroutine for background execution."""
        task = BackgroundTask(
            name=name,
            goal=goal,
            status=TaskStatus.PENDING,
        )
        self._tasks[task.task_id] = task

        async_handle = asyncio.create_task(
            self._execute_custom_job(task, coro_func, *args, **kwargs)
        )
        self._async_handles[task.task_id] = async_handle
        return task

    async def _execute_orchestrator_task(
        self,
        task: BackgroundTask,
        context: Optional[str],
        auto_approve_safe: bool,
    ) -> None:
        """Run task through Unified Orchestrator with live progress tracking."""
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        task.logs.append(f"[{time.strftime('%H:%M:%S')}] Task started: {task.name}")

        try:
            # 1. Progress update
            task.progress = 0.2
            task.logs.append(f"[{time.strftime('%H:%M:%S')}] Planning and component selection initiated...")

            # 2. Execute via Orchestrator
            res = await self.orchestrator.run(
                goal=task.goal,
                context=context,
                auto_approve_safe=auto_approve_safe,
                record_memory=True,
            )

            task.progress = 1.0
            task.completed_at = time.time()
            task.result = res.final_output

            if res.success:
                task.status = TaskStatus.COMPLETED
                task.logs.append(f"[{time.strftime('%H:%M:%S')}] Task completed successfully in {res.total_duration_seconds:.2f}s")
                self.notifications.notify(
                    type="task_completed",
                    title=f"Task Completed: {task.name}",
                    message=f"Autonomous task '{task.name}' finished successfully.",
                    severity=NotificationSeverity.SUCCESS,
                    metadata={"task_id": task.task_id},
                )
            else:
                task.status = TaskStatus.FAILED
                task.error = res.error or "Orchestrator reported step failure"
                task.logs.append(f"[{time.strftime('%H:%M:%S')}] Task failed: {task.error}")
                self.notifications.notify(
                    type="task_failed",
                    title=f"Task Failed: {task.name}",
                    message=f"Autonomous task '{task.name}' failed: {task.error}",
                    severity=NotificationSeverity.WARNING,
                    metadata={"task_id": task.task_id},
                )

        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            task.completed_at = time.time()
            task.logs.append(f"[{time.strftime('%H:%M:%S')}] Task cancelled by user.")
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = time.time()
            task.logs.append(f"[{time.strftime('%H:%M:%S')}] Exception: {str(e)}")
            self.notifications.notify(
                type="task_failed",
                title=f"Task Error: {task.name}",
                message=str(e),
                severity=NotificationSeverity.CRITICAL,
                metadata={"task_id": task.task_id},
            )

    async def _execute_custom_job(
        self,
        task: BackgroundTask,
        coro_func: Callable,
        *args,
        **kwargs,
    ) -> None:
        """Run custom coroutine in background."""
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        try:
            task.progress = 0.5
            res = await coro_func(*args, **kwargs)
            task.progress = 1.0
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()
            task.result = str(res)
        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            task.completed_at = time.time()
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = time.time()

    def get_task(self, task_id: str) -> Optional[BackgroundTask]:
        return self._tasks.get(task_id)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 50,
    ) -> List[BackgroundTask]:
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks[:limit]

    def cancel_task(self, task_id: str) -> bool:
        """Cancel an in-progress background task."""
        handle = self._async_handles.get(task_id)
        task = self._tasks.get(task_id)
        if handle and not handle.done():
            handle.cancel()
            if task:
                task.status = TaskStatus.CANCELLED
                task.completed_at = time.time()
            return True
        return False


# Global singleton background task manager
BACKGROUND_TASK_MANAGER = BackgroundTaskManager()

