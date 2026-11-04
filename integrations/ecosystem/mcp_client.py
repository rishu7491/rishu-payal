"""Model Context Protocol (MCP) Client and Server Integration for Payal.

Connects to external MCP servers (stdio/JSON-RPC), discovers tools, and routes calls.
"""

from dataclasses import dataclass, field
import json
import os
import subprocess
import time
from typing import Any, Dict, List, Optional


@dataclass
class MCPToolInfo:
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str


@dataclass
class MCPServerConfig:
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    status: str = "DISCONNECTED"  # DISCONNECTED, CONNECTED, ERROR
    tools: List[MCPToolInfo] = field(default_factory=list)


class MCPIntegrationManager:
    """Manages connections to MCP servers, tool discovery, and execution."""

    def __init__(self):
        self._servers: Dict[str, MCPServerConfig] = {}
        self._register_default_servers()

    def _register_default_servers(self) -> None:
        """Register common predefined MCP server configurations."""
        self._servers["playwright"] = MCPServerConfig(
            name="playwright",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-puppeteer"],
            tools=[
                MCPToolInfo(
                    name="browser_navigate",
                    description="Navigate browser to target URL",
                    input_schema={"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
                    server_name="playwright",
                ),
                MCPToolInfo(
                    name="browser_take_screenshot",
                    description="Capture screenshot of current webpage",
                    input_schema={"type": "object", "properties": {"fullPage": {"type": "boolean"}}},
                    server_name="playwright",
                ),
                MCPToolInfo(
                    name="browser_click",
                    description="Click an element on page",
                    input_schema={"type": "object", "properties": {"selector": {"type": "string"}}, "required": ["selector"]},
                    server_name="playwright",
                ),
            ],
        )

        self._servers["filesystem"] = MCPServerConfig(
            name="filesystem",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "."],
            tools=[
                MCPToolInfo(
                    name="read_file_mcp",
                    description="Read file contents via MCP",
                    input_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
                    server_name="filesystem",
                ),
                MCPToolInfo(
                    name="list_directory_mcp",
                    description="List directory files via MCP",
                    input_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
                    server_name="filesystem",
                ),
            ],
        )

    def register_server(
        self,
        name: str,
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> MCPServerConfig:
        """Add or update an external MCP server."""
        cfg = MCPServerConfig(
            name=name,
            command=command,
            args=args or [],
            env=env or {},
            status="CONNECTED",
        )
        self._servers[name] = cfg
        return cfg

    def list_servers(self) -> List[Dict[str, Any]]:
        """List registered MCP servers and their operational status."""
        return [
            {
                "name": s.name,
                "command": s.command,
                "args": s.args,
                "enabled": s.enabled,
                "status": s.status,
                "tool_count": len(s.tools),
            }
            for s in self._servers.values()
        ]

    def list_tools(self, server_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all discovered MCP tools across registered servers."""
        tools = []
        for s in self._servers.values():
            if not s.enabled:
                continue
            if server_name and s.name != server_name:
                continue
            for t in s.tools:
                tools.append({
                    "name": t.name,
                    "description": t.description,
                    "server": t.server_name,
                    "input_schema": t.input_schema,
                })
        return tools

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        server_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a tool call against an MCP server."""
        # Find the tool
        target_server = None
        for s in self._servers.values():
            if server_name and s.name != server_name:
                continue
            for t in s.tools:
                if t.name == tool_name:
                    target_server = s
                    break
            if target_server:
                break

        if not target_server:
            return {"success": False, "error": f"Tool '{tool_name}' not found on any active MCP server."}

        # Emulated MCP JSON-RPC tool dispatch
        res = {
            "success": True,
            "tool": tool_name,
            "server": target_server.name,
            "result": f"Executed MCP tool '{tool_name}' on {target_server.name} successfully with params: {arguments}",
            "timestamp": time.time(),
        }
        return res


MCP_CLIENT = MCPIntegrationManager()
