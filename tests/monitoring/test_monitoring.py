"""Unit tests for Phase 8 Security, Health, Audit, and Disaster Recovery."""

import asyncio
import pytest
from core.monitoring import (
    SECURITY_MONITOR,
    HEALTH_MONITOR,
    AUDIT_LOGGER,
    CIRCUIT_BREAKER,
    BACKUP_MANAGER,
)


def test_security_monitor():
    # Safe check
    safe_eval = SECURITY_MONITOR.evaluate_action(
        action="read_file",
        target="data/readme.txt",
    )
    assert safe_eval["allowed"] is True
    assert safe_eval["blocked"] is False

    # Dangerous check (e.g., destructive command or sensitive ssh key)
    dang_eval = SECURITY_MONITOR.evaluate_action(
        action="cat",
        target="/root/.ssh/id_rsa",
    )
    assert dang_eval["blocked"] is True
    assert dang_eval["severity"] == "HIGH"

    incidents = SECURITY_MONITOR.get_incidents()
    assert len(incidents) > 0


def test_health_monitor():
    async def run_async():
        report = await HEALTH_MONITOR.get_full_health_report()
        assert report["status"] in ["healthy", "degraded"]
        assert "resources" in report
        assert "database" in report
        assert "models" in report

    asyncio.run(run_async())


def test_audit_logger():
    entry = AUDIT_LOGGER.log(
        event_type="test_event",
        action="validate_test",
        target="pytest_runner",
        status="SUCCESS",
        details={"test": True},
    )
    assert entry.entry_id.startswith("aud-")
    assert entry.checksum != ""

    records = AUDIT_LOGGER.query(event_type="test_event", limit=5)
    assert any(r["entry_id"] == entry.entry_id for r in records)


def test_circuit_breaker():
    res_name = "test_flaky_service"
    CIRCUIT_BREAKER.reset_all()
    assert CIRCUIT_BREAKER.can_execute(res_name) is True

    # Record 3 failures
    CIRCUIT_BREAKER.record_failure(res_name)
    CIRCUIT_BREAKER.record_failure(res_name)
    trip_info = CIRCUIT_BREAKER.record_failure(res_name)
    assert trip_info["tripped"] is True
    assert CIRCUIT_BREAKER.can_execute(res_name) is False

    # Reset
    CIRCUIT_BREAKER.record_success(res_name)
    assert CIRCUIT_BREAKER.can_execute(res_name) is True


def test_backup_and_restore():
    backup = BACKUP_MANAGER.create_backup(tag="test_snap")
    assert backup["success"] is True
    assert backup["filename"].endswith(".zip")

    backups = BACKUP_MANAGER.list_backups()
    assert any(b["filename"] == backup["filename"] for b in backups)
