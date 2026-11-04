"""Payal Autonomous Policy Engine.

Enforces zero-trust boundaries, decides autonomous vs approval-required actions,
and protects user data from destructive operations.
"""

from enum import Enum
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from execution.tools.schemas import PermissionLevel, ToolCategory


class ActionRiskLevel(str, Enum):
    """Risk tiers for autonomous decision-making."""
    SAFE = "safe"          # Read-only, inspection, query -> Fully autonomous
    LOW = "low"            # Non-destructive workspace operations, tests -> Autonomous
    HIGH = "high"          # Code write/overwrite, terminal execution, system modifications -> Approval required
    CRITICAL = "critical"  # File deletion, credential modifications, external egress -> Explicit approval


class PolicyDecision(BaseModel):
    """Result of policy evaluation for a proposed action."""
    allowed: bool
    requires_approval: bool
    risk_level: ActionRiskLevel
    reason: str
    rule_name: str
    action_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class PolicyEngine:
    """Evaluates operations against security policies and user trust rules."""

    # Patterns indicating high destructive risk
    DESTRUCTIVE_COMMAND_PATTERNS = [
        r"\brm\s+-rf\b",
        r"\bdel\s+/[sS]\b",
        r"\bRemove-Item\b.*-Recurse",
        r"\bformat\b",
        r"\bdrop\s+database\b",
        r"\bdrop\s+table\b",
        r"\btruncate\b",
        r"\bshutdown\b",
        r"\breboot\b",
        r"\bgit\s+reset\s+--hard\b",
        r"\bgit\s+push\s+.*--force\b",
    ]

    # Sensitive targets that can never be modified autonomously
    SENSITIVE_TARGETS = [
        r"\.env",
        r"credentials",
        r"id_rsa",
        r"\.git/",
        r"settings\.json",
    ]

    def __init__(self, autonomous_mode: bool = True):
        self.autonomous_mode = autonomous_mode

    def evaluate_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        category: Optional[ToolCategory] = None,
        permission_level: Optional[PermissionLevel] = None,
        action_type: str = "TOOL",
    ) -> PolicyDecision:
        """Evaluate a proposed action (TOOL, AGENT, SKILL, COMMAND)."""
        # Advisory / generative agent & skill invocations are safe
        if action_type in ["AGENT", "SKILL"]:
            return PolicyDecision(
                allowed=True,
                requires_approval=False,
                risk_level=ActionRiskLevel.SAFE,
                reason=f"{action_type} invocation is advisory and safe for autonomous execution.",
                rule_name="ALLOW_AGENT_SKILL_ADVISORY",
                action_type=tool_name,
                parameters=arguments,
            )

        # 1. Critical target check (credentials, system keys)
        target_str = str(arguments)
        for pattern in self.SENSITIVE_TARGETS:
            if re.search(pattern, target_str, re.IGNORECASE):
                return PolicyDecision(
                    allowed=True,
                    requires_approval=True,
                    risk_level=ActionRiskLevel.CRITICAL,
                    reason=f"Action accesses sensitive target matching '{pattern}'.",
                    rule_name="PROTECT_SENSITIVE_TARGETS",
                    action_type=tool_name,
                    parameters=arguments,
                )

        # 2. Terminal commands risk evaluation
        if tool_name in ["powershell_exec", "terminal_exec", "bash_exec"]:
            command = arguments.get("command", "")
            for pattern in self.DESTRUCTIVE_COMMAND_PATTERNS:
                if re.search(pattern, command, re.IGNORECASE):
                    return PolicyDecision(
                        allowed=True,
                        requires_approval=True,
                        risk_level=ActionRiskLevel.CRITICAL,
                        reason=f"Terminal command contains destructive pattern: '{pattern}'.",
                        rule_name="BLOCK_DESTRUCTIVE_COMMANDS",
                        action_type=tool_name,
                        parameters=arguments,
                    )

            # Normal terminal command (compile, test, status)
            return PolicyDecision(
                allowed=True,
                requires_approval=True,
                risk_level=ActionRiskLevel.HIGH,
                reason="Terminal command execution requires operator approval.",
                rule_name="REQUIRE_APPROVAL_FOR_TERMINAL",
                action_type=tool_name,
                parameters=arguments,
            )

        # 3. Read-only tools
        if tool_name in ["read_file", "list_directory", "inspect_component", "search_skills"]:
            return PolicyDecision(
                allowed=True,
                requires_approval=False,
                risk_level=ActionRiskLevel.SAFE,
                reason="Read-only operation is safe for autonomous execution.",
                rule_name="ALLOW_READ_ONLY",
                action_type=tool_name,
                parameters=arguments,
            )

        # 4. Workspace writing
        if tool_name in ["write_file", "edit_file", "create_file"]:
            return PolicyDecision(
                allowed=True,
                requires_approval=not self.autonomous_mode,
                risk_level=ActionRiskLevel.LOW if self.autonomous_mode else ActionRiskLevel.HIGH,
                reason="File modification inside project workspace.",
                rule_name="GOVERN_WORKSPACE_WRITES",
                action_type=tool_name,
                parameters=arguments,
            )

        # 5. Permission level based fallback
        if permission_level == PermissionLevel.LEVEL_1_READ_ONLY:
            return PolicyDecision(
                allowed=True,
                requires_approval=False,
                risk_level=ActionRiskLevel.SAFE,
                reason="Level 1 read-only operation.",
                rule_name="ALLOW_LEVEL_1",
                action_type=tool_name,
                parameters=arguments,
            )

        if permission_level == PermissionLevel.LEVEL_2_WORKSPACE_REVERSIBLE:
            return PolicyDecision(
                allowed=True,
                requires_approval=False,
                risk_level=ActionRiskLevel.LOW,
                reason="Level 2 workspace reversible operation.",
                rule_name="ALLOW_LEVEL_2",
                action_type=tool_name,
                parameters=arguments,
            )

        # High level / default requires approval
        return PolicyDecision(
            allowed=True,
            requires_approval=True,
            risk_level=ActionRiskLevel.HIGH,
            reason=f"Action '{tool_name}' requires operational approval.",
            rule_name="DEFAULT_GOVERNANCE",
            action_type=tool_name,
            parameters=arguments,
        )


# Global singleton policy engine
POLICY_ENGINE = PolicyEngine(autonomous_mode=True)

