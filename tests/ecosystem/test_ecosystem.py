"""Unit tests for Phase 9 Ecosystem, MCP, Plugins, and Web Automation."""

import asyncio
import pytest
from integrations.ecosystem import (
    MCP_CLIENT,
    WEB_AUTOMATION,
    PLUGIN_MANAGER,
)


def test_mcp_client():
    async def run_async():
        servers = MCP_CLIENT.list_servers()
        assert len(servers) >= 2
        assert any(s["name"] == "playwright" for s in servers)

        tools = MCP_CLIENT.list_tools()
        assert len(tools) >= 3
        assert any(t["name"] == "browser_navigate" for t in tools)

        call_res = await MCP_CLIENT.call_tool(
            tool_name="browser_navigate",
            arguments={"url": "https://example.com"},
        )
        assert call_res["success"] is True
        assert "Executed MCP tool" in call_res["result"]

    asyncio.run(run_async())


def test_plugin_manager():
    async def run_async():
        plugins = PLUGIN_MANAGER.list_plugins()
        assert len(plugins) >= 3
        assert any(p["id"] == "github" for p in plugins)

        # Execute capability
        res = await PLUGIN_MANAGER.execute_plugin("github", "list_repos")
        assert res["success"] is True
        assert "rishu-payal" in res["result"]["repos"]

        # Toggle status
        PLUGIN_MANAGER.set_plugin_status("github", False)
        blocked_res = await PLUGIN_MANAGER.execute_plugin("github", "list_repos")
        assert blocked_res["success"] is False
        assert "disabled" in blocked_res["error"]

        # Re-enable
        PLUGIN_MANAGER.set_plugin_status("github", True)

    asyncio.run(run_async())


def test_web_automation():
    async def run_async():
        nav_res = await WEB_AUTOMATION.navigate("https://example.com")
        assert nav_res.url == "https://example.com"
        assert isinstance(nav_res.content_text, str)

    asyncio.run(run_async())
