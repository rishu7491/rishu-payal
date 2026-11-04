"""Scheduler Engine for Payal Automation."""

import asyncio
import time
from typing import Dict, List, Optional

from .background import BACKGROUND_TASK_MANAGER, BackgroundTaskManager
from .models import BackgroundTask, ScheduledJob, ScheduleType


class TaskScheduler:
    """Manages recurring, delayed, and cron-like automated tasks."""

    def __init__(
        self,
        task_manager: Optional[BackgroundTaskManager] = None,
        tick_interval: float = 5.0,
    ):
        self.task_manager = task_manager or BACKGROUND_TASK_MANAGER
        self.tick_interval = tick_interval
        self._jobs: Dict[str, ScheduledJob] = {}
        self._ticker_task: Optional[asyncio.Task] = None
        self._is_running = False

    def add_job(
        self,
        name: str,
        goal: str,
        schedule_type: ScheduleType = ScheduleType.INTERVAL,
        interval_seconds: float = 3600.0,
        delay_seconds: float = 0.0,
        cron_expr: Optional[str] = None,
    ) -> ScheduledJob:
        """Register a new scheduled job."""
        now = time.time()
        next_run = now + delay_seconds if delay_seconds > 0 else (now + interval_seconds)

        job = ScheduledJob(
            name=name,
            goal=goal,
            schedule_type=schedule_type,
            interval_seconds=interval_seconds,
            cron_expr=cron_expr,
            next_run=next_run,
            is_active=True,
        )
        self._jobs[job.job_id] = job
        return job

    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job."""
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False

    def schedule_interval(
        self,
        name: str,
        interval_seconds: float,
        goal: str,
    ) -> ScheduledJob:
        """Convenience method to register a recurring interval task."""
        return self.add_job(
            name=name,
            goal=goal,
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=interval_seconds,
        )

    def cancel_job(self, job_id: str) -> bool:
        """Alias for remove_job."""
        return self.remove_job(job_id)

    def pause_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job:
            job.is_active = False
            return True
        return False

    def resume_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job:
            job.is_active = True
            job.next_run = time.time() + job.interval_seconds
            return True
        return False

    def get_job(self, job_id: str) -> Optional[ScheduledJob]:
        return self._jobs.get(job_id)

    def list_jobs(self, active_only: bool = False) -> List[ScheduledJob]:
        jobs = list(self._jobs.values())
        if active_only:
            jobs = [j for j in jobs if j.is_active]
        return jobs

    def check_and_trigger(self, current_time: Optional[float] = None) -> List[BackgroundTask]:
        """Evaluate scheduled jobs and trigger overdue executions."""
        now = current_time or time.time()
        triggered_tasks: List[BackgroundTask] = []

        for job in list(self._jobs.values()):
            if not job.is_active:
                continue

            if now >= job.next_run:
                # Dispatch background task
                task = self.task_manager.submit_task(
                    name=f"[Scheduled] {job.name}",
                    goal=job.goal,
                )
                triggered_tasks.append(task)

                job.last_run = now
                job.run_count += 1

                if job.schedule_type == ScheduleType.ONCE:
                    job.is_active = False
                else:
                    job.next_run = now + job.interval_seconds

        return triggered_tasks

    async def _run_ticker(self) -> None:
        """Background loop ticking schedules."""
        while self._is_running:
            try:
                self.check_and_trigger()
            except Exception:
                pass
            await asyncio.sleep(self.tick_interval)

    def start(self) -> None:
        """Start async scheduler ticker loop."""
        if not self._is_running:
            self._is_running = True
            try:
                self._ticker_task = asyncio.create_task(self._run_ticker())
            except RuntimeError:
                pass

    def stop(self) -> None:
        """Stop scheduler loop."""
        self._is_running = False
        if self._ticker_task and not self._ticker_task.done():
            self._ticker_task.cancel()


# Global singleton task scheduler
TASK_SCHEDULER = TaskScheduler()

