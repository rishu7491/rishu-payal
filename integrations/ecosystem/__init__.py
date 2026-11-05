"""Payal Ecosystem and External Integrations Module.

Provides MCP Client, Web Automation, and Modular Plugin Extensibility.
"""

from .mcp_client import (
    MCPServerConfig,
    MCPToolInfo,
    MCPIntegrationManager,
    MCP_CLIENT,
)
from .web_automation import (
    PageNavigationResult,
    WebAutomationEngine,
    WEB_AUTOMATION,
)
from .plugins import (
    BasePlugin,
    PluginMetadata,
    PluginManager,
    PLUGIN_MANAGER,
)

__all__ = [
    "MCPServerConfig",
    "MCPToolInfo",
    "MCPIntegrationManager",
    "MCP_CLIENT",
    "PageNavigationResult",
    "WebAutomationEngine",
    "WEB_AUTOMATION",
    "BasePlugin",
    "PluginMetadata",
    "PluginManager",
    "PLUGIN_MANAGER",
]

