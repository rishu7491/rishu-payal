"""Ecosystem, MCP, Plugins, and Web Integration API routes for Payal."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from integrations.ecosystem import (
    PLUGIN_MANAGER,
    MCP_CLIENT,
    WEB_AUTOMATION,
)

router = APIRouter(prefix="/api/ecosystem", tags=["ecosystem"])


class TogglePluginRequest(BaseModel):
    enabled: bool = Field(..., description="Enable or disable this plugin")


class ExecutePluginRequest(BaseModel):
    action: str = Field(..., description="Action name to execute")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Action parameters")


class RegisterMCPServerRequest(BaseModel):
    name: str = Field(..., description="Unique server name")
    command: str = Field(..., description="Executable command e.g. npx, python")
    args: Optional[List[str]] = Field(default_factory=list, description="Command arguments")
    env: Optional[Dict[str, str]] = Field(default_factory=dict, description="Environment variables")


class CallMCPToolRequest(BaseModel):
    tool_name: str = Field(..., description="Name of MCP tool")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments for tool")
    server_name: Optional[str] = Field(None, description="Optional target server name")


class WebNavigateRequest(BaseModel):
    url: str = Field(..., description="Web URL to navigate and extract")
    timeout: int = Field(default=10, description="Request timeout in seconds")


@router.get("/plugins")
async def list_plugins() -> Dict[str, Any]:
    """List all registered external plugins and their statuses."""
    plugins = PLUGIN_MANAGER.list_plugins()
    return {"status": "success", "count": len(plugins), "plugins": plugins}


@router.post("/plugins/{plugin_id}/toggle")
async def toggle_plugin(plugin_id: str, req: TogglePluginRequest) -> Dict[str, Any]:
    """Enable or disable a specific plugin."""
    success = PLUGIN_MANAGER.set_plugin_status(plugin_id, req.enabled)
    if not success:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")
    return {"status": "success", "plugin_id": plugin_id, "enabled": req.enabled}


@router.post("/plugins/{plugin_id}/execute")
async def execute_plugin_action(plugin_id: str, req: ExecutePluginRequest) -> Dict[str, Any]:
    """Execute an action on a registered plugin."""
    res = await PLUGIN_MANAGER.execute_plugin(plugin_id, req.action, req.params)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Execution failed"))
    return {"status": "success", "data": res.get("result")}


@router.get("/mcp/servers")
async def list_mcp_servers() -> Dict[str, Any]:
    """List registered Model Context Protocol (MCP) servers."""
    servers = MCP_CLIENT.list_servers()
    return {"status": "success", "servers": servers}


@router.post("/mcp/servers")
async def register_mcp_server(req: RegisterMCPServerRequest) -> Dict[str, Any]:
    """Register or update an external MCP server."""
    cfg = MCP_CLIENT.register_server(
        name=req.name,
        command=req.command,
        args=req.args,
        env=req.env,
    )
    return {"status": "success", "server": req.name, "status": cfg.status}


@router.get("/mcp/tools")
async def list_mcp_tools(server: Optional[str] = None) -> Dict[str, Any]:
    """List discovered MCP tools across servers."""
    tools = MCP_CLIENT.list_tools(server_name=server)
    return {"status": "success", "count": len(tools), "tools": tools}


@router.post("/mcp/tools/call")
async def call_mcp_tool_endpoint(req: CallMCPToolRequest) -> Dict[str, Any]:
    """Call an MCP tool on an external server."""
    res = await MCP_CLIENT.call_tool(
        tool_name=req.tool_name,
        arguments=req.arguments,
        server_name=req.server_name,
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Tool execution failed"))
    return {"status": "success", "tool_result": res}


@router.post("/web/navigate")
async def navigate_web_page(req: WebNavigateRequest) -> Dict[str, Any]:
    """Navigate to a webpage and extract clean textual content."""
    res = await WEB_AUTOMATION.navigate(req.url, timeout=req.timeout)
    if not res.success:
        raise HTTPException(status_code=502, detail=res.error or "Navigation error")
    return {
        "status": "success",
        "url": res.url,
        "title": res.title,
        "status_code": res.status_code,
        "content_preview": res.content_text,
        "duration_seconds": res.duration_seconds,
    }
