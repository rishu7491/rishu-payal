"""Execution Plan and Step schemas for Payal Autonomous Planner."""

import time
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    """A discrete, executable step within an overall task execution plan."""
    step_id: str = Field(default_factory=lambda: f"step_{uuid.uuid4().hex[:6]}")
    title: str
    action_type: str = "AGENT"  # "AGENT", "TOOL", "SKILL", "COMMAND"
    target_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    risk_level: str = "SAFE"  # "SAFE", "LOW", "HIGH", "CRITICAL"
    expected_outcome: str = ""


class ExecutionPlan(BaseModel):
    """Structured plan dividing a high-level goal into actionable steps."""
    plan_id: str = Field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:8]}")
    goal: str
    context: Optional[str] = None
    steps: List[PlanStep] = Field(default_factory=list)
    primary_agent: Optional[str] = None
    supporting_skills: List[str] = Field(default_factory=list)
    rule_suites: List[str] = Field(default_factory=list)
    estimated_risk: str = "SAFE"
    created_at: float = Field(default_factory=time.time)

