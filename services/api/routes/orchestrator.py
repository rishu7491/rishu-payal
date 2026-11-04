"""API routes for Autonomous Task Orchestrator."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.orchestrator import UNIFIED_ORCHESTRATOR
from core.planner import TASK_PLANNER

router = APIRouter(prefix="/api/orchestrate", tags=["Orchestrator"])


class OrchestrationRequest(BaseModel):
    goal: str = Field(..., description="High-level goal or task to plan and execute")
    context: Optional[str] = Field(default=None, description="Additional project context or constraints")
    auto_approve_safe: bool = Field(default=True, description="Automatically approve SAFE and LOW risk steps")
    record_memory: bool = Field(default=True, description="Record execution summary into long-term memory")


class PlanPreviewRequest(BaseModel):
    goal: str = Field(..., description="Goal to decompose into an execution plan")
    context: Optional[str] = Field(default=None, description="Optional context")


@router.post("")
async def run_orchestration(req: OrchestrationRequest):
    """Execute the end-to-end Autonomous Execution Pipeline:
    Input → Memory Retrieval → Context Building → Orchestrator → Execution → Memory Update.
    """
    try:
        result = await UNIFIED_ORCHESTRATOR.run(
            goal=req.goal,
            context=req.context,
            auto_approve_safe=req.auto_approve_safe,
            record_memory=req.record_memory,
        )
        return {
            "goal": result.goal,
            "success": result.success,
            "plan": result.plan.model_dump(),
            "step_results": [
                {
                    "step_id": r.step_id,
                    "target_name": r.target_name,
                    "action_type": r.action_type,
                    "success": r.success,
                    "approval_status": r.approval_status,
                    "duration_seconds": r.duration_seconds,
                    "output": r.output[:1000] if r.output else "",
                    "error": r.error,
                }
                for r in result.step_results
            ],
            "final_output": result.final_output,
            "total_duration_seconds": result.total_duration_seconds,
            "error": result.error,
            "summary": result.summary,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plan")
async def preview_plan(req: PlanPreviewRequest):
    """Preview a decomposed ExecutionPlan without running execution."""
    try:
        plan = await TASK_PLANNER.create_plan(goal=req.goal, context=req.context)
        return plan.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
