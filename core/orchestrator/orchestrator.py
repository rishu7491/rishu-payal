"""Payal Unified Orchestrator.

Implements the end-to-end Autonomous Execution Engine pipeline:
User Goal → Planner → Component Selection → Policy Engine → Execution Runtime → Verification Engine → Final Result.
"""

from dataclasses import dataclass, field
import time
from typing import Any, Dict, List, Optional

from core.planner.schemas import ExecutionPlan, PlanStep
from execution.runtime import EXECUTION_RUNTIME, ExecutionRuntime, StepExecutionRequest, StepExecutionResult
from execution.verification import VERIFICATION_ENGINE, VerificationEngine
from .selector import COMPONENT_SELECTOR, ComponentSelector, ComponentSelection


@dataclass
class OrchestrationResult:
    """Final output and trace of an autonomous orchestration session."""
    goal: str
    plan: ExecutionPlan
    step_results: List[StepExecutionResult] = field(default_factory=list)
    final_output: str = ""
    success: bool = True
    total_duration_seconds: float = 0.0
    error: Optional[str] = None
    selection: Optional[ComponentSelection] = None
    summary: Dict[str, Any] = field(default_factory=dict)


class UnifiedOrchestrator:
    """Coordinates autonomous execution across ECC components, tools, and verification."""

    def __init__(
        self,
        planner=None,
        selector=None,
        runtime: Optional[ExecutionRuntime] = None,
        verifier: Optional[VerificationEngine] = None,
        memory=None,
    ):
        self._planner = planner
        self._selector = selector
        self.runtime = runtime or EXECUTION_RUNTIME
        self.verifier = verifier or VERIFICATION_ENGINE
        self._memory = memory

    @property
    def planner(self):
        if self._planner is None:
            from core.planner.planner import TASK_PLANNER
            self._planner = TASK_PLANNER
        return self._planner

    @property
    def selector(self):
        if self._selector is None:
            from core.orchestrator.selector import COMPONENT_SELECTOR
            self._selector = COMPONENT_SELECTOR
        return self._selector

    @property
    def memory(self):
        if self._memory is None:
            from core.memory import MEMORY_MANAGER
            self._memory = MEMORY_MANAGER
        return self._memory

    async def run(
        self,
        goal: str,
        context: Optional[str] = None,
        auto_approve_safe: bool = True,
        max_recovery_retries: int = 1,
        record_memory: bool = True,
    ) -> OrchestrationResult:
        """Execute the full autonomous pipeline for a user goal:
        Input → Memory Retrieval → Context Building → Orchestrator → Execution → Memory Update.
        """
        start_time = time.time()

        # 1. Memory Retrieval & Context Building
        active_context = self.memory.prepare_task_context(goal=goal, base_context=context)

        # 2. Component Selection
        selection = self.selector.select(goal, active_context)

        # 3. Plan Creation
        plan = await self.planner.create_plan(goal, active_context)

        # Record plan overview in Context Manager (Tier L1)
        plan_summary_text = f"Plan ID: {plan.plan_id} | Steps: {len(plan.steps)} | Risk: {plan.estimated_risk}"
        self.memory.context.set_l1(
            plan_summary=plan_summary_text,
            components=plan.supporting_skills[:5],
        )

        step_results: List[StepExecutionResult] = []
        overall_success = True
        orchestration_error = None

        # 4. Execution Loop with Policy Gating & Verification
        for step in plan.steps:
            req = StepExecutionRequest(
                step_id=step.step_id,
                action_type=step.action_type,
                target_name=step.target_name,
                arguments=step.arguments,
                context=self.memory.context.build_context(),
                expected_outcome=step.expected_outcome,
            )

            result = await self.runtime.execute_step(
                request=req,
                auto_approve_safe=auto_approve_safe,
            )

            # 5. Recovery & Self-Correction if step failed or verification failed
            if (not result.success or (result.verification and not result.verification.success)) and max_recovery_retries > 0:
                retries = 0
                while retries < max_recovery_retries:
                    retries += 1
                    correction_prompt = (
                        f"Previous execution of '{step.target_name}' encountered an issue:\n"
                        f"Error: {result.error}\n"
                        f"Verification issues: {result.verification.failed_checks if result.verification else 'None'}\n"
                        f"Please rectify and regenerate the output."
                    )
                    recovery_args = dict(step.arguments)
                    recovery_args["prompt"] = f"{recovery_args.get('prompt', '')}\n\n[Correction Request]: {correction_prompt}"

                    recovery_req = StepExecutionRequest(
                        step_id=f"{step.step_id}_retry_{retries}",
                        action_type=step.action_type,
                        target_name=step.target_name,
                        arguments=recovery_args,
                        context=self.memory.context.build_context(),
                        expected_outcome=step.expected_outcome,
                    )

                    recovery_res = await self.runtime.execute_step(
                        request=recovery_req,
                        auto_approve_safe=auto_approve_safe,
                    )
                    recovery_res.recovery_attempts = retries

                    if recovery_res.success and (not recovery_res.verification or recovery_res.verification.success):
                        result = recovery_res
                        break
                    result = recovery_res

            step_results.append(result)

            # Record step outcome into L2 detail tier
            self.memory.context.append_l2(
                detail_type=f"{step.action_type}:{step.target_name}",
                content=result.output or (result.error or "No output"),
            )

            if not result.success:
                overall_success = False
                orchestration_error = f"Step '{step.title}' failed: {result.error}"
                break

        # 6. Synthesize Final Result
        final_output = self._synthesize_final_output(goal, plan, step_results, overall_success)

        # 7. Memory Update: Persistent Long-term Task Recording
        if record_memory:
            self.memory.record_task_completion(
                goal=goal,
                summary=f"Executed {len(step_results)} steps with status {'SUCCESS' if overall_success else 'FAILED'}",
                components_used=[plan.primary_agent or ""] + plan.supporting_skills[:4],
                outcome=final_output[:500],
                success=overall_success,
            )

        total_duration = time.time() - start_time
        summary = {
            "total_steps": len(plan.steps),
            "executed_steps": len(step_results),
            "successful_steps": sum(1 for r in step_results if r.success),
            "primary_agent": plan.primary_agent,
            "supporting_skills": plan.supporting_skills,
            "rule_suites": plan.rule_suites,
            "memory_recorded": record_memory,
        }

        return OrchestrationResult(
            goal=goal,
            plan=plan,
            step_results=step_results,
            final_output=final_output,
            success=overall_success,
            total_duration_seconds=total_duration,
            error=orchestration_error,
            selection=selection,
            summary=summary,
        )

    def _synthesize_final_output(
        self,
        goal: str,
        plan: ExecutionPlan,
        step_results: List[StepExecutionResult],
        success: bool,
    ) -> str:
        """Synthesize a structured executive summary of the orchestrated execution."""
        if not step_results:
            return f"Orchestration concluded with no executed steps for goal: {goal}"

        # If last step was a code review or verification step, include its output prominently
        last_step = step_results[-1]
        sections = [
            f"# Autonomous Execution Report: {goal}\n",
            f"**Status:** {'COMPLETED' if success else 'FAILED'}",
            f"**Primary Agent:** `{plan.primary_agent}`",
            f"**Components Utilized:** {', '.join(plan.supporting_skills[:4]) or 'Standard Runtime'}\n",
            "## Execution Steps:",
        ]

        for idx, res in enumerate(step_results, 1):
            status_icon = "PASS" if res.success else "FAIL"
            approval = f"[{res.approval_status}]" if res.approval_status != "AUTO_APPROVED" else ""
            sections.append(f"{idx}. **[{status_icon}] {res.target_name}** ({res.action_type}) {approval} - {res.duration_seconds:.2f}s")

        sections.append("\n## Final Synthesized Result:\n")
        sections.append(last_step.output or "No output generated.")

        return "\n".join(sections)


# Global singleton orchestrator
UNIFIED_ORCHESTRATOR = UnifiedOrchestrator()
