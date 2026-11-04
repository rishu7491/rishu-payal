"""Tests for Components, Memory, and Orchestrator API routes."""

from fastapi.testclient import TestClient
import pytest

from services.api.app import app
from core.model_router.base import ModelProvider
from core.model_router.router import ROUTER
from core.model_router.schemas import CompletionRequest, CompletionResponse, ProviderHealth


class FakeApiProvider(ModelProvider):
    def __init__(self):
        self.name = "fake_api_prov"

    async def generate(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(
            content="API simulated response: Plan executed and verified.",
            model="test-model",
            provider=self.name,
        )

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(provider=self.name, available=True, latency_ms=1.0)

    async def list_models(self) -> list[str]:
        return ["test-model"]


@pytest.fixture(autouse=True)
def setup_fake_router():
    """Ensure the global router has a responsive provider during API testing."""
    original_providers = dict(ROUTER.providers)
    original_primary = ROUTER.primary_provider
    fake = FakeApiProvider()
    ROUTER.providers["fake_api"] = fake
    ROUTER.primary_provider = "fake_api"
    yield
    ROUTER.providers = original_providers
    ROUTER.primary_provider = original_primary


client = TestClient(app)


def test_components_stats_api():
    """Verify /api/components/stats returns catalog counts."""
    res = client.get("/api/components/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["total_skills"] >= 300
    assert data["total_agents"] >= 70
    assert data["total_rule_suites"] >= 20
    assert data["total_commands"] >= 90


def test_components_agents_and_skills_api():
    """Verify listing and searching agents and skills."""
    res_agents = client.get("/api/components/agents?limit=5")
    assert res_agents.status_code == 200
    assert len(res_agents.json()) == 5

    res_skills = client.get("/api/components/skills?q=python&limit=3")
    assert res_skills.status_code == 200
    assert len(res_skills.json()) >= 1


def test_memory_crud_api():
    """Verify full CRUD lifecycle on /api/memory."""
    # 1. Create
    create_payload = {
        "title": "API Test Fact",
        "content": "Payal uses 314 skills and 71 agents.",
        "kind": "fact",
        "scope": "project",
        "tags": ["test", "api"],
        "importance": 0.75,
    }
    create_res = client.post("/api/memory", json=create_payload)
    assert create_res.status_code == 200
    mem_data = create_res.json()
    mem_id = mem_data["id"]
    assert mem_data["title"] == "API Test Fact"

    # 2. Get by ID
    get_res = client.get(f"/api/memory/{mem_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == mem_id

    # 3. Update
    update_res = client.put(f"/api/memory/{mem_id}", json={"importance": 0.99})
    assert update_res.status_code == 200
    assert update_res.json()["importance"] == 0.99

    # 4. Search
    search_res = client.post("/api/memory/search", json={"query": "314 skills", "limit": 5})
    assert search_res.status_code == 200
    found = search_res.json()
    assert any(m["id"] == mem_id for m in found)

    # 5. Delete
    del_res = client.delete(f"/api/memory/{mem_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"

    # 6. Verify 404 after delete
    assert client.get(f"/api/memory/{mem_id}").status_code == 404


def test_memory_context_inspection():
    """Verify /api/memory/context returns tiered context details."""
    res = client.get("/api/memory/context")
    assert res.status_code == 200
    data = res.json()
    assert "l0_abstract" in data
    assert "l1_overview" in data
    assert "l2_detail" in data


def test_orchestrator_plan_preview_api():
    """Verify /api/orchestrate/plan previews an execution plan."""
    req_body = {
        "goal": "Build an encrypted password storage vault",
        "context": "Must use AES-256-GCM",
    }
    res = client.post("/api/orchestrate/plan", json=req_body)
    assert res.status_code == 200
    data = res.json()
    assert "plan_id" in data
    assert len(data["steps"]) >= 2
    assert data["primary_agent"] is not None


def test_orchestrator_run_api():
    """Verify /api/orchestrate executes end-to-end and returns response."""
    req_body = {
        "goal": "Draft API contract for password reset",
        "auto_approve_safe": True,
        "record_memory": True,
    }
    res = client.post("/api/orchestrate", json=req_body)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["step_results"]) >= 2
    assert "final_output" in data
    assert data["summary"]["memory_recorded"] is True
