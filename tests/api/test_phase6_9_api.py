"""Integration tests for Phase 6-9 REST API endpoints."""

from fastapi.testclient import TestClient
import pytest
from services.api.app import app

client = TestClient(app)


def test_automation_api():
    # Notifications
    res = client.get("/api/automation/notifications")
    assert res.status_code == 200
    data = res.json()
    assert "unread_count" in data

    # Schedules
    res = client.get("/api/automation/schedules")
    assert res.status_code == 200

    # Proactive suggestions
    res = client.get("/api/automation/suggestions")
    assert res.status_code == 200


def test_multimodal_api():
    # Screen permission status
    res = client.get("/api/multimodal/screen/status")
    assert res.status_code == 200
    assert "permission_granted" in res.json()

    # Voice speech synthesis
    res = client.post(
        "/api/multimodal/synthesize",
        json={"text": "Namaste Rishabh, Payal is ready.", "emotion": "happy"},
    )
    assert res.status_code == 200
    assert res.json()["speech"]["emotion"] == "happy"

    # Vision analysis
    res = client.post(
        "/api/multimodal/vision/analyze",
        json={"image_data": "dGVzdF9pbWFnZQ==", "prompt": "Analyze UI components"},
    )
    assert res.status_code == 200
    assert res.json()["vision"]["success"] is True


def test_monitoring_api():
    # Health
    res = client.get("/api/monitoring/health")
    assert res.status_code == 200
    assert "health" in res.json()

    # Audit
    res = client.get("/api/monitoring/audit")
    assert res.status_code == 200

    # Security evaluation
    res = client.post(
        "/api/monitoring/security/evaluate",
        json={"action": "rmdir", "target": "C:\\Windows\\System32"},
    )
    assert res.status_code == 200
    assert res.json()["evaluation"]["blocked"] is True

    # Backups list
    res = client.get("/api/monitoring/backups")
    assert res.status_code == 200


def test_ecosystem_api():
    # Plugins
    res = client.get("/api/ecosystem/plugins")
    assert res.status_code == 200
    assert res.json()["count"] >= 3

    # MCP Tools
    res = client.get("/api/ecosystem/mcp/tools")
    assert res.status_code == 200
    assert res.json()["count"] >= 3

    # MCP Servers
    res = client.get("/api/ecosystem/mcp/servers")
    assert res.status_code == 200
