"""Payal Approval Manager.

Tracks, audits, and manages approvals for sensitive or high-impact actions.
"""

from dataclasses import dataclass, field
import time
import uuid
from typing import Any, Dict, List, Optional
from .policy import ActionRiskLevel, PolicyDecision


@dataclass
class ApprovalRequest:
    """Pending or resolved authorization request."""
    request_id: str
    action_type: str
    target: str
    parameters: Dict[str, Any]
    risk_level: ActionRiskLevel
    reason: str
    status: str = "PENDING"  # PENDING, APPROVED, DENIED, EXPIRED
    created_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None
    resolved_by: Optional[str] = None
    resolution_note: Optional[str] = None


class ApprovalManager:
    """Handles operator approval lifecycle for actions gated by policy."""

    def __init__(self, auto_approve_safe_actions: bool = True):
        self.auto_approve_safe_actions = auto_approve_safe_actions
        self.requests: Dict[str, ApprovalRequest] = {}

    def create_request(
        self,
        decision: PolicyDecision,
        target: str = "",
        request_id: Optional[str] = None,
    ) -> ApprovalRequest:
        """Create and register a new approval request."""
        req_id = request_id or f"apr_{uuid.uuid4().hex[:8]}"
        req = ApprovalRequest(
            request_id=req_id,
            action_type=decision.action_type,
            target=target or str(decision.parameters),
            parameters=decision.parameters,
            risk_level=decision.risk_level,
            reason=decision.reason,
            status="PENDING",
        )
        self.requests[req_id] = req
        return req

    def approve(self, request_id: str, operator: str = "user") -> bool:
        """Approve a pending request."""
        req = self.requests.get(request_id)
        if not req or req.status != "PENDING":
            return False

        req.status = "APPROVED"
        req.resolved_at = time.time()
        req.resolved_by = operator
        return True

    def deny(self, request_id: str, reason: str = "", operator: str = "user") -> bool:
        """Deny a pending request."""
        req = self.requests.get(request_id)
        if not req or req.status != "PENDING":
            return False

        req.status = "DENIED"
        req.resolved_at = time.time()
        req.resolved_by = operator
        req.resolution_note = reason
        return True

    def get_pending(self) -> List[ApprovalRequest]:
        """Return list of all currently pending approval requests."""
        return [r for r in self.requests.values() if r.status == "PENDING"]

    def should_auto_approve(self, decision: PolicyDecision) -> bool:
        """Check if an action can be auto-approved based on risk."""
        if not decision.requires_approval:
            return True

        if self.auto_approve_safe_actions and decision.risk_level in [
            ActionRiskLevel.SAFE,
            ActionRiskLevel.LOW,
        ]:
            return True

        return False


# Global singleton approval manager
APPROVAL_MANAGER = ApprovalManager(auto_approve_safe_actions=True)

