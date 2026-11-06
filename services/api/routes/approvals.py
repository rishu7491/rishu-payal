"""Real Security Approvals and Policy Gating API for Payal."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.monitoring.audit_logger import AUDIT_LOGGER
from execution.permissions.approval import APPROVAL_MANAGER, ApprovalRequest
from execution.permissions.policy import ActionRiskLevel, PolicyDecision

router = APIRouter(prefix="/api/approvals", tags=["Approvals"])


class ApprovalDecisionRequest(BaseModel):
    approved: bool = Field(..., description="True to authorize, False to deny")
    note: Optional[str] = Field(default=None, description="Optional operator reason")


def _seed_initial_pending_if_empty():
    """Seed one real pending approval if none exist for demonstration."""
    if not APPROVAL_MANAGER.requests:
        decision = PolicyDecision(
            allowed=False,
            requires_approval=True,
            risk_level=ActionRiskLevel.HIGH,
            rule_name="REQUIRE_CACHE_CLEAR_APPROVAL",
            action_type="CLEAR_BROWSER_CACHE",
            reason="Operator approval required before clearing browser cache, session cookies, and temporary data.",
            parameters={"target": "browser_cache", "impact": "temporary session logout"},
        )
        APPROVAL_MANAGER.create_request(decision, target="Google Chrome & Edge Cache", request_id="apr_cache_clear")


@router.get("/pending")
async def get_pending_approvals() -> Dict[str, Any]:
    """Retrieve all pending security approvals requiring user authorization."""
    _seed_initial_pending_if_empty()
    pending = APPROVAL_MANAGER.get_pending()
    items = []
    for r in pending:
        items.append({
            "request_id": r.request_id,
            "action_type": r.action_type,
            "target": r.target,
            "risk_level": r.risk_level.name if hasattr(r.risk_level, "name") else str(r.risk_level),
            "reason": r.reason,
            "parameters": r.parameters,
            "status": r.status,
            "created_at": r.created_at,
        })
    return {"status": "success", "count": len(items), "pending": items}


@router.post("/{request_id}/decision")
async def resolve_approval(request_id: str, req: ApprovalDecisionRequest) -> Dict[str, Any]:
    """Approve or reject a pending security action with audit ledger recording."""
    if req.approved:
        success = APPROVAL_MANAGER.approve(request_id, operator="Rishu")
        new_status = "APPROVED"
    else:
        success = APPROVAL_MANAGER.deny(request_id, reason=req.note or "Rejected by user", operator="Rishu")
        new_status = "DENIED"

    if not success:
        raise HTTPException(status_code=404, detail=f"Pending approval request '{request_id}' not found.")

    AUDIT_LOGGER.log(
        event_type="APPROVAL_DECISION",
        actor="Rishu",
        action=f"resolve_{request_id}",
        target=request_id,
        status=new_status,
        details={"note": req.note, "approved": req.approved},
    )

    return {
        "status": "success",
        "request_id": request_id,
        "decision": new_status,
        "message": f"Action {new_status.lower()} and committed to audit ledger.",
    }


@router.get("/history")
async def get_approval_history() -> Dict[str, Any]:
    """Retrieve full history of resolved approval requests."""
    resolved = [r for r in APPROVAL_MANAGER.requests.values() if r.status != "PENDING"]
    items = []
    for r in resolved:
        items.append({
            "request_id": r.request_id,
            "action_type": r.action_type,
            "target": r.target,
            "risk_level": r.risk_level.name if hasattr(r.risk_level, "name") else str(r.risk_level),
            "status": r.status,
            "resolved_by": r.resolved_by,
            "resolved_at": r.resolved_at,
            "note": r.resolution_note,
        })
    return {"status": "success", "count": len(items), "history": items}
