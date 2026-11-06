from fastapi.testclient import TestClient
import pytest

from services.api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_devices_list(client):
    response = client.get("/api/devices")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "devices" in data
    assert data["total_count"] >= 3
    names = [d["name"] for d in data["devices"]]
    assert "Windows Laptop" in names
    assert "Personal Phone" in names


def test_device_heartbeat(client):
    payload = {
        "device_id": "personal_phone",
        "name": "Personal Phone",
        "device_type": "android",
        "battery": 92,
        "ip": "10.196.121.182",
        "status": "online",
    }
    response = client.post("/api/devices/heartbeat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["device_id"] == "personal_phone"
    assert data["online"] is True


def test_approvals_pending_and_decision(client):
    res = client.get("/api/approvals/pending")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "pending" in data
    assert len(data["pending"]) >= 1

    req_id = data["pending"][0]["request_id"]
    res_dec = client.post(f"/api/approvals/{req_id}/decision", json={"approved": True, "note": "Test approval"})
    assert res_dec.status_code == 200
    dec_data = res_dec.json()
    assert dec_data["status"] == "success"
    assert dec_data["decision"] == "APPROVED"
    assert dec_data["request_id"] == req_id


def test_automation_tasks_toggle(client):
    res = client.get("/api/automation/tasks")
    assert res.status_code == 200
    tasks = res.json()
    assert len(tasks) > 0

    task_id = tasks[0]["task_id"]
    res_toggle = client.post(f"/api/automation/tasks/{task_id}/toggle?done=true")
    assert res_toggle.status_code == 200
    data = res_toggle.json()
    assert data["status"] == "completed"
