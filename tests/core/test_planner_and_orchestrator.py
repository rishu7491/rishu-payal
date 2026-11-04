"""Tests for Task Planner, Component Selector, and Unified Orchestrator."""

import pytest
from core.model_router.base import ModelProvider
from core.model_router.router import ModelRouter
from core.model_router.schemas import CompletionRequest, CompletionResponse, ProviderHealth
from core.orchestrator.selector import ComponentSelector
from core.planner.planner import TaskPlanner
from core.orchestrator.orchestrator import UnifiedOrchestrator
from core.memory.manager import MemoryManager
from core.memory.storage import PersistentMemoryStore
from core.memory.context_manager import ContextManager
from core.memory.retriever import MemoryRetriever
from execution.runtime import ExecutionRuntime
from execution.permissions.policy import PolicyEngine
from execution.permissions.approval import ApprovalManager
from execution.verification import VerificationEngine
from integrations.ecc.registry import ECC_REGISTRY
from integrations.ecc.runner import ECCRunner


class FakeOrchestratorProvider(ModelProvider):
    def __init__(self):
        self.name = "fake_orchestrator_prov"

    async def generate(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(
            content="Execution output: Requirements analyzed and verified successfully.",
            model="fake-model",
            provider=self.name,
        )

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(provider=self.name, available=True, latency_ms=5.0)

    async def list_models(self) -> list[str]:
        return ["fake-model"]


@pytest.fixture
def fake_router():
    provider = FakeOrchestratorProvider()
    return ModelRouter(config=None, providers={"fake": provider}, primary_provider="fake")


def test_component_selector_domains():
    """Verify ComponentSelector detects domains and matches ECC agents and skills."""
    selector = ComponentSelector(registry=ECC_REGISTRY)

    # 1. Frontend Goal
    fe_sel = selector.select("Design a responsive React dashboard with modern Tailwind styling")
    assert fe_sel.primary_agent is not None
    assert any("react" in a.name or "design" in a.name or "architect" in a.name for a in [fe_sel.primary_agent] + fe_sel.supporting_agents)
    assert any("react" in s.name or "design" in s.name or "frontend" in s.name for s in fe_sel.recommended_skills)

    # 2. Security Goal
    sec_sel = selector.select("Perform penetration testing and vulnerability audit on API endpoints")
    assert sec_sel.primary_agent is not None
    assert any("security" in a.name or "hunter" in a.name or "architect" in a.name for a in [sec_sel.primary_agent] + sec_sel.supporting_agents)

    # 3. Backend Goal
    be_sel = selector.select("Optimize SQL database queries and FastAPI server endpoints")
    assert be_sel.primary_agent is not None
    assert any("fastapi" in a.name or "database" in a.name or "architect" in a.name for a in [be_sel.primary_agent] + be_sel.supporting_agents)


@pytest.mark.anyio
async def test_task_planner_creation(fake_router):
    """Verify TaskPlanner produces an actionable multi-step ExecutionPlan."""
    planner = TaskPlanner(router=fake_router)
    plan = await planner.create_plan("Build user login and registration API")

    assert plan.plan_id.startswith("plan_")
    assert len(plan.steps) >= 2
    assert plan.primary_agent is not None
    assert plan.steps[0].action_type in ["AGENT", "TOOL", "SKILL"]
    assert plan.steps[0].risk_level in ["SAFE", "LOW", "HIGH", "CRITICAL"]


@pytest.mark.anyio
async def test_unified_orchestrator_pipeline(tmp_path, fake_router):
    """Verify end-to-end Orchestrator execution with memory persistence."""
    store = PersistentMemoryStore(db_path=tmp_path / "orch_test_mem.db")
    ctx = ContextManager()
    retriever = MemoryRetriever(store=store)
    mem_mgr = MemoryManager(store=store, context=ctx, retriever=retriever)

    ecc_runner = ECCRunner(registry=ECC_REGISTRY, router=fake_router)
    runtime = ExecutionRuntime(
        policy_engine=PolicyEngine(),
        approval_manager=ApprovalManager(),
        verification_engine=VerificationEngine(),
        ecc_runner=ecc_runner,
    )
    planner = TaskPlanner(router=fake_router)
    orchestrator = UnifiedOrchestrator(
        planner=planner,
        runtime=runtime,
        memory=mem_mgr,
    )

    result = await orchestrator.run(
        goal="Generate Python utility module for date parsing",
        auto_approve_safe=True,
        record_memory=True,
    )

    assert result.success is True
    assert len(result.step_results) >= 2
    assert "Autonomous Execution Report" in result.final_output
    assert result.total_duration_seconds > 0.0

    # Verify task was durably recorded in memory
    saved_tasks = store.list(kind="task_summary")
    assert len(saved_tasks) == 1
    assert "date parsing" in saved_tasks[0].title.lower()
