"""Payal Autonomous Execution Runtime.

Executes selected agents, skills, and tools governed by the Policy Engine,
gated by the Approval Manager, and verified by the Verification Engine.
"""

from dataclasses import dataclass, field
import time
from typing import Any, Dict, List, Optional
import uuid

from execution.permissions.policy import ActionRiskLevel, PolicyDecision, PolicyEngine, POLICY_ENGINE
from execution.permissions.approval import ApprovalManager, APPROVAL_MANAGER
from execution.tools.registry import ToolRegistry
from execution.verification import VerificationEngine, VerificationResult, VERIFICATION_ENGINE
from execution.windows.powershell_adapter import PowerShellAdapter
from execution.linux.kali_adapter import KaliAdapter
from integrations.ecc.runner import ECCRunner, ECC_RUNNER


@dataclass
class StepExecutionRequest:
    """Request to execute a single atomic step."""
    step_id: str
    action_type: str  # "TOOL", "AGENT", "SKILL", "COMMAND"
    target_name: str  # e.g., "powershell_exec", "architect", "accessibility"
    arguments: Dict[str, Any] = field(default_factory=dict)
    context: Optional[str] = None
    expected_outcome: Optional[str] = None


@dataclass
class StepExecutionResult:
    """Outcome of an executed atomic step."""
    step_id: str
    action_type: str
    target_name: str
    output: str
    success: bool
    policy_decision: Optional[PolicyDecision] = None
    approval_status: str = "AUTO_APPROVED"
    verification: Optional[VerificationResult] = None
    duration_seconds: float = 0.0
    error: Optional[str] = None
    recovery_attempts: int = 0


class ExecutionRuntime:
    """Unified runtime coordinating Policy, Approval, Execution, and Verification."""

    def __init__(
        self,
        policy_engine: Optional[PolicyEngine] = None,
        approval_manager: Optional[ApprovalManager] = None,
        verification_engine: Optional[VerificationEngine] = None,
        ecc_runner: Optional[ECCRunner] = None,
        powershell_adapter: Optional[PowerShellAdapter] = None,
        kali_adapter: Optional[KaliAdapter] = None,
    ):
        self.policy = policy_engine or POLICY_ENGINE
        self.approval = approval_manager or APPROVAL_MANAGER
        self.verifier = verification_engine or VERIFICATION_ENGINE
        self.ecc_runner = ecc_runner or ECC_RUNNER
        self.powershell = powershell_adapter or PowerShellAdapter()
        self.kali = kali_adapter or KaliAdapter()

    async def execute_step(
        self,
        request: StepExecutionRequest,
        auto_approve_safe: bool = True,
        max_recovery_retries: int = 1,
    ) -> StepExecutionResult:
        """Execute a step with policy gating, tool/agent dispatch, and output verification."""
        start_time = time.time()

        # 1. Evaluate Policy
        decision = self.policy.evaluate_tool_call(
            tool_name=request.target_name,
            arguments=request.arguments,
            action_type=request.action_type,
        )

        # 2. Check Approval Requirements
        approval_status = "AUTO_APPROVED"
        if decision.requires_approval:
            if auto_approve_safe and self.approval.should_auto_approve(decision):
                approval_status = "AUTO_APPROVED_SAFE"
            else:
                # Must create an approval request and hold execution
                app_req = self.approval.create_request(decision, target=request.target_name)
                return StepExecutionResult(
                    step_id=request.step_id,
                    action_type=request.action_type,
                    target_name=request.target_name,
                    output="",
                    success=False,
                    policy_decision=decision,
                    approval_status=f"PENDING_APPROVAL:{app_req.request_id}",
                    error=f"Execution halted: Action requires approval ({decision.reason}).",
                    duration_seconds=time.time() - start_time,
                )

        # 3. Dispatch Execution
        output = ""
        success = True
        error = None

        try:
            if request.action_type == "AGENT":
                user_prompt = request.arguments.get("prompt", "")
                agent_res = await self.ecc_runner.call_agent(
                    agent_name=request.target_name,
                    user_prompt=user_prompt,
                    context=request.context,
                )
                output = agent_res.output
                success = agent_res.success
                error = agent_res.error

            elif request.action_type == "SKILL":
                script_name = request.arguments.get("script")
                args = request.arguments.get("args", [])
                skill_res = await self.ecc_runner.run_skill(
                    skill_name=request.target_name,
                    script_name=script_name,
                    args=args,
                )
                output = skill_res.output
                success = skill_res.success
                error = skill_res.error

            elif request.action_type == "COMMAND":
                user_input = request.arguments.get("input", "")
                cmd_res = await self.ecc_runner.run_command(
                    command_name=request.target_name,
                    user_input=user_input,
                )
                output = cmd_res.output
                success = cmd_res.success
                error = cmd_res.error

            elif request.action_type == "TOOL":
                # Built-in PowerShell / Terminal adapter execution
                if request.target_name == "powershell_exec":
                    cmd = request.arguments.get("command", "")
                    cwd = request.arguments.get("cwd")
                    timeout = int(request.arguments.get("timeout", 60))
                    res = await self.powershell.execute(command=cmd, cwd=cwd, timeout=timeout)
                    output = res["stdout"] or res["stderr"]
                    success = res["success"]
                    error = res["stderr"] if not success else None

                elif request.target_name == "kali_exec":
                    cmd = request.arguments.get("command", "")
                    res = self.kali._run_cmd(cmd.split())
                    output = res["stdout"] or res["stderr"]
                    success = res["success"]
                    error = res["stderr"] if not success else None

                elif request.target_name == "read_file":
                    path = request.arguments.get("path", "")
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        output = f.read()
                    success = True

                elif request.target_name == "write_file":
                    path = request.arguments.get("path", "")
                    content = request.arguments.get("content", "")
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(content)
                    output = f"File successfully written: {path}"
                    success = True

                else:
                    output = f"Tool '{request.target_name}' executed."
                    success = True
            else:
                success = False
                error = f"Unsupported action type: {request.action_type}"

        except Exception as e:
            success = False
            error = str(e)

        # 4. Verification Check
        verification = None
        if success and output:
            if request.action_type == "AGENT":
                verification = self.verifier.verify_agent_output(output)
            elif request.target_name == "powershell_exec":
                verification = self.verifier.verify_command_output(
                    exit_code=0 if success else 1,
                    stdout=output,
                    stderr=error or "",
                )

        duration = time.time() - start_time
        return StepExecutionResult(
            step_id=request.step_id,
            action_type=request.action_type,
            target_name=request.target_name,
            output=output,
            success=success,
            policy_decision=decision,
            approval_status=approval_status,
            verification=verification,
            duration_seconds=duration,
            error=error,
        )


# Global singleton execution runtime
EXECUTION_RUNTIME = ExecutionRuntime()

