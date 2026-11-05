"""Monitoring, Health, Security, and Disaster Recovery API routes for Payal."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.monitoring import (
    HEALTH_MONITOR,
    SECURITY_MONITOR,
    AUDIT_LOGGER,
    CIRCUIT_BREAKER,
    BACKUP_MANAGER,
)

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


class EvaluateActionRequest(BaseModel):
    action: str = Field(..., description="Action name or command")
    target: str = Field(..., description="Target file, URL, or process")
    arguments: Optional[Dict[str, Any]] = None


class CreateBackupRequest(BaseModel):
    tag: Optional[str] = Field(None, description="Optional backup tag or note")


class RestoreBackupRequest(BaseModel):
    backup_name: str = Field(..., description="Name of the backup zip file to restore")


@router.get("/health")
async def get_system_health() -> Dict[str, Any]:
    """Retrieve full health status of AI models, databases, OS subsystems, and disk."""
    report = await HEALTH_MONITOR.get_full_health_report()
    return {"status": "success", "health": report}


@router.get("/security/incidents")
async def list_security_incidents(
    limit: int = Query(50, ge=1, le=200),
    severity: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """List monitored security alerts and potential policy violations."""
    incidents = SECURITY_MONITOR.get_incidents(limit=limit, severity=severity)
    return {"status": "success", "count": len(incidents), "incidents": incidents}


@router.post("/security/evaluate")
async def evaluate_security_action(req: EvaluateActionRequest) -> Dict[str, Any]:
    """Pre-flight security check on an action or command."""
    res = SECURITY_MONITOR.evaluate_action(
        action=req.action,
        target=req.target,
        arguments=req.arguments,
    )
    return {"status": "success", "evaluation": res}


@router.get("/audit")
async def get_audit_trail(
    limit: int = Query(50, ge=1, le=200),
    event_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Query immutable audit ledger."""
    entries = AUDIT_LOGGER.query(event_type=event_type, status=status, limit=limit)
    return {"status": "success", "count": len(entries), "audit_entries": entries}


@router.get("/recovery/breakers")
async def list_circuit_breakers() -> Dict[str, Any]:
    """Inspect all active service circuit breakers and recovery cooldowns."""
    breakers = CIRCUIT_BREAKER.list_status()
    return {"status": "success", "circuit_breakers": breakers}


@router.post("/recovery/reset")
async def reset_circuit_breakers() -> Dict[str, Any]:
    """Reset all tripped circuit breakers to CLOSED state."""
    CIRCUIT_BREAKER.reset_all()
    return {"status": "success", "message": "All circuit breakers reset to CLOSED"}


@router.post("/backup")
async def create_system_backup(req: CreateBackupRequest = CreateBackupRequest()) -> Dict[str, Any]:
    """Create a compressed snapshot of memory database and configurations."""
    res = BACKUP_MANAGER.create_backup(tag=req.tag)
    AUDIT_LOGGER.log(
        event_type="system_backup",
        action="create_backup",
        target=res.get("filename", "unknown"),
        status="SUCCESS",
        details=res,
    )
    return {"status": "success", "backup": res}


@router.get("/backups")
async def list_system_backups() -> Dict[str, Any]:
    """List all available system backups."""
    backups = BACKUP_MANAGER.list_backups()
    return {"status": "success", "count": len(backups), "backups": backups}


@router.post("/restore")
async def restore_system_backup(req: RestoreBackupRequest) -> Dict[str, Any]:
    """Restore memory DB and configuration from a snapshot backup."""
    res = BACKUP_MANAGER.restore_backup(req.backup_name)
    if not res.get("success"):
        AUDIT_LOGGER.log(
            event_type="system_restore",
            action="restore_backup",
            target=req.backup_name,
            status="FAILED",
            details=res,
        )
        raise HTTPException(status_code=400, detail=res.get("error", "Restore failed"))

    AUDIT_LOGGER.log(
        event_type="system_restore",
        action="restore_backup",
        target=req.backup_name,
        status="SUCCESS",
        details=res,
    )
    return {"status": "success", "restore_result": res}

