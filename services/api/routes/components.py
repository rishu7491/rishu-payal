"""API endpoints for querying loaded ECC Components (314 skills, 71 agents, etc.)."""

from typing import List, Optional
from fastapi import APIRouter, Query

from integrations.ecc.registry import ECC_REGISTRY, ECCRegistry

router = APIRouter(prefix="/api/components", tags=["Components"])


@router.get("/stats")
async def get_component_stats():
    """Retrieve catalog statistics across all integrated ECC assets."""
    return ECC_REGISTRY.get_stats().model_dump()


@router.get("/agents")
async def list_agents(
    q: Optional[str] = Query(None, description="Search keyword"),
    limit: int = Query(20, ge=1, le=100),
):
    """List or search registered ECC agents."""
    if q:
        agents = ECC_REGISTRY.search_agents(q, limit=limit)
    else:
        agents = ECC_REGISTRY.list_agents()[:limit]
    return [a.model_dump() for a in agents]


@router.get("/skills")
async def list_skills(
    q: Optional[str] = Query(None, description="Search keyword"),
    limit: int = Query(20, ge=1, le=100),
):
    """List or search registered ECC skills."""
    if q:
        skills = ECC_REGISTRY.search_skills(q, limit=limit)
    else:
        skills = ECC_REGISTRY.list_skills()[:limit]
    return [s.model_dump() for s in skills]


@router.get("/rules")
async def list_rules():
    """List all available rule suites."""
    suites = ECC_REGISTRY.list_rule_suites()
    return [{"name": s.name, "folder_path": s.folder_path, "categories": list(s.rules.keys())} for s in suites]


@router.get("/commands")
async def list_commands(limit: int = Query(50, ge=1, le=100)):
    """List registered ECC slash and CLI commands."""
    commands = ECC_REGISTRY.list_commands()[:limit]
    return [c.model_dump() for c in commands]
