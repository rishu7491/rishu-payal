"""Unit tests for Phase 6 Proactive Intelligence and Automation Engine."""

import asyncio
import pytest
from core.automation import (
    BACKGROUND_TASK_MANAGER,
    TASK_SCHEDULER,
    PROACTIVE_ENGINE,
    NOTIFICATION_HUB,
    NotificationSeverity,
)


def test_notification_hub():
    initial_count = NOTIFICATION_HUB.get_unread_count()
    notif = NOTIFICATION_HUB.notify(
        type="system_backup",
        title="Test Alert",
        message="System backup ready",
        severity=NotificationSeverity.INFO,
    )
    assert notif.title == "Test Alert"
    assert NOTIFICATION_HUB.get_unread_count() == initial_count + 1

    marked = NOTIFICATION_HUB.mark_as_read(notif.id)
    assert marked is True
    assert NOTIFICATION_HUB.get_unread_count() == initial_count


def test_background_task_manager():
    async def sample_work():
        return "Async computation done"

    async def run():
        task = BACKGROUND_TASK_MANAGER.submit_job(
            name="test_async_job",
            goal="Execute test computation",
            coro_func=sample_work,
        )
        assert task.name == "test_async_job"
        assert task.status.value in ["pending", "running", "completed"]

        fetched = BACKGROUND_TASK_MANAGER.get_task(task.task_id)
        assert fetched is not None
        assert fetched.task_id == task.task_id

    asyncio.run(run())


def test_task_scheduler():
    job = TASK_SCHEDULER.schedule_interval(
        name="periodic_health_pulse",
        interval_seconds=60,
        goal="Run health check",
    )
    assert job.name == "periodic_health_pulse"
    assert job.interval_seconds == 60

    active_jobs = TASK_SCHEDULER.list_jobs()
    assert any(j.job_id == job.job_id for j in active_jobs)

    # Cancel job
    cancelled = TASK_SCHEDULER.cancel_job(job.job_id)
    assert cancelled is True


def test_proactive_intelligence_engine():
    async def run():
        report = await PROACTIVE_ENGINE.run_proactive_cycle(force=True)
        assert report.success is True
        assert report.observations is not None
        assert isinstance(report.suggestions, list)
        assert report.cycle_duration_seconds >= 0.0

    asyncio.run(run())
