"""Task Planner for Payal Autonomous Execution Engine.

Decomposes complex user goals into structured, executable steps,
assigning appropriate ECC agents, skills, and tools with dependency tracking.
"""

import json
import re
from typing import Any, Dict, List, Optional
import uuid

from core.model_router.router import ROUTER
from core.model_router.schemas import ChatMessage, CompletionRequest
from .schemas import ExecutionPlan, PlanStep


class TaskPlanner:
    """Plans multi-step execution graphs for autonomous task completion."""

    def __init__(self, selector=None, router=None):
        self._selector = selector
        self.router = router or ROUTER

    @property
    def selector(self):
        if self._selector is None:
            from core.orchestrator.selector import COMPONENT_SELECTOR
            self._selector = COMPONENT_SELECTOR
        return self._selector

    async def create_plan(self, goal: str, context: Optional[str] = None) -> ExecutionPlan:
        """Generate an execution plan decomposing the goal into actionable steps."""
        selection = self.selector.select(goal, context)

        # Attempt LLM-assisted decomposition first
        llm_plan = await self._generate_llm_plan(goal, context, selection)
        if llm_plan:
            return llm_plan

        # Fallback to deterministic heuristic plan
        return self._generate_heuristic_plan(goal, context, selection)

    async def _generate_llm_plan(
        self,
        goal: str,
        context: Optional[str],
        selection: Any,
    ) -> Optional[ExecutionPlan]:
        """Attempt to decompose using ModelRouter with JSON output."""
        primary_agent_name = selection.primary_agent.name if selection.primary_agent else "agency-software-architect"
        skills_summary = ", ".join(s.name for s in selection.recommended_skills[:5])
        rules_summary = ", ".join(r.name for r in selection.applicable_rules[:3])

        system_prompt = (
            "You are the Payal Task Planner. Decompose the user's goal into a precise JSON execution plan.\n"
            "Return strictly valid JSON with this exact schema:\n"
            "{\n"
            '  "estimated_risk": "SAFE" | "LOW" | "HIGH" | "CRITICAL",\n'
            '  "steps": [\n'
            '    {\n'
            '      "step_id": "step_1",\n'
            '      "title": "Short title",\n'
            '      "action_type": "AGENT" | "TOOL" | "SKILL" | "COMMAND",\n'
            '      "target_name": "agent or tool name",\n'
            '      "arguments": { "prompt": "..." },\n'
            '      "dependencies": [],\n'
            '      "risk_level": "SAFE" | "LOW" | "HIGH" | "CRITICAL",\n'
            '      "expected_outcome": "Expected result description"\n'
            '    }\n'
            '  ]\n'
            "}"
        )

        user_content = (
            f"Goal: {goal}\n"
            f"Context: {context or 'None'}\n"
            f"Primary Agent: {primary_agent_name}\n"
            f"Candidate Skills: {skills_summary}\n"
            f"Candidate Rules: {rules_summary}"
        )

        req = CompletionRequest(
            messages=[
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_content),
            ],
            temperature=0.2,
        )

        try:
            resp = await self.router.generate(req)
            raw = resp.content.strip()
            # Extract JSON block if wrapped in markdown
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
            json_str = match.group(1) if match else raw
            data = json.loads(json_str)

            steps: List[PlanStep] = []
            for item in data.get("steps", []):
                step = PlanStep(
                    step_id=item.get("step_id", f"step_{uuid.uuid4().hex[:6]}"),
                    title=item.get("title", "Plan Step"),
                    action_type=item.get("action_type", "AGENT"),
                    target_name=item.get("target_name", primary_agent_name),
                    arguments=item.get("arguments", {}),
                    dependencies=item.get("dependencies", []),
                    risk_level=item.get("risk_level", "SAFE"),
                    expected_outcome=item.get("expected_outcome", ""),
                )
                steps.append(step)

            if steps:
                return ExecutionPlan(
                    goal=goal,
                    context=context,
                    steps=steps,
                    primary_agent=primary_agent_name,
                    supporting_skills=[s.name for s in selection.recommended_skills],
                    rule_suites=[r.name for r in selection.applicable_rules],
                    estimated_risk=data.get("estimated_risk", "LOW"),
                )
        except Exception:
            pass

        return None

    def _generate_heuristic_plan(
        self,
        goal: str,
        context: Optional[str],
        selection: Any,
    ) -> ExecutionPlan:
        """Create a robust 3-stage plan: Spec/Design -> Execution -> Verification."""
        primary_agent_name = selection.primary_agent.name if selection.primary_agent else "architect"
        supporting_agent_names = [a.name for a in selection.supporting_agents]
        reviewer_name = "code-reviewer" if "code-reviewer" in supporting_agent_names else ("code-reviewer" if self.selector.registry.get_agent("code-reviewer") else primary_agent_name)

        step_1_id = f"step_{uuid.uuid4().hex[:4]}_plan"
        step_2_id = f"step_{uuid.uuid4().hex[:4]}_exec"
        step_3_id = f"step_{uuid.uuid4().hex[:4]}_verify"

        steps = [
            PlanStep(
                step_id=step_1_id,
                title=f"Analyze and design: {goal[:50]}",
                action_type="AGENT",
                target_name=primary_agent_name,
                arguments={
                    "prompt": f"Analyze requirements and formulate implementation specifications for: {goal}",
                    "context": context,
                },
                dependencies=[],
                risk_level="SAFE",
                expected_outcome="Detailed technical specification and execution strategy",
            ),
            PlanStep(
                step_id=step_2_id,
                title=f"Execute core task: {goal[:50]}",
                action_type="AGENT",
                target_name=supporting_agent_names[0] if supporting_agent_names else primary_agent_name,
                arguments={
                    "prompt": f"Implement the requested solution for: {goal}",
                    "context": context,
                },
                dependencies=[step_1_id],
                risk_level="LOW",
                expected_outcome="Working implementation artifacts or actionable response",
            ),
            PlanStep(
                step_id=step_3_id,
                title="Verify implementation and quality compliance",
                action_type="AGENT",
                target_name=reviewer_name,
                arguments={
                    "prompt": f"Review and verify the completed output for: {goal}. Check correctness, security, and edge cases.",
                    "context": context,
                },
                dependencies=[step_2_id],
                risk_level="SAFE",
                expected_outcome="Verification report confirming quality and correctness",
            ),
        ]

        return ExecutionPlan(
            goal=goal,
            context=context,
            steps=steps,
            primary_agent=primary_agent_name,
            supporting_skills=[s.name for s in selection.recommended_skills],
            rule_suites=[r.name for r in selection.applicable_rules],
            estimated_risk="LOW",
        )


# Global singleton planner
TASK_PLANNER = TaskPlanner()
