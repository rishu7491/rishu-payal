"""Modular Plugin and Integration System for Payal AI."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import time
from typing import Any, Dict, List, Optional


@dataclass
class PluginMetadata:
    plugin_id: str
    name: str
    version: str
    description: str
    author: str = "Rishabh Raj"
    capabilities: List[str] = field(default_factory=list)
    enabled: bool = True
    config_schema: Dict[str, Any] = field(default_factory=dict)


class BasePlugin(ABC):
    """Abstract interface for all Payal ecosystem plugins."""

    def __init__(self, metadata: PluginMetadata):
        self.metadata = metadata
        self.config: Dict[str, Any] = {}

    @property
    def plugin_id(self) -> str:
        return self.metadata.plugin_id

    @property
    def is_enabled(self) -> bool:
        return self.metadata.enabled

    def enable(self) -> None:
        self.metadata.enabled = True

    def disable(self) -> None:
        self.metadata.enabled = False

    def configure(self, settings: Dict[str, Any]) -> None:
        self.config.update(settings)

    @abstractmethod
    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific plugin capability."""
        pass


class GitHubPlugin(BasePlugin):
    """Integrates with GitHub for repository management, commits, and pull requests."""

    def __init__(self):
        super().__init__(
            PluginMetadata(
                plugin_id="github",
                name="GitHub Integration",
                version="1.0.0",
                description="Manage GitHub repositories, issues, branches, and commits.",
                capabilities=["list_repos", "get_repo_info", "create_issue", "check_status"],
            )
        )

    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "list_repos":
            return {"repos": ["rishu-payal", "Agent"], "status": "success"}
        elif action == "get_repo_info":
            repo = params.get("repo", "rishu-payal")
            return {"repo": repo, "owner": "rishu7491", "private": True, "branch": "main"}
        return {"action": action, "status": "executed", "params": params}


class NotionPlugin(BasePlugin):
    """Integrates with Notion for workspace notes, databases, and task docs."""

    def __init__(self):
        super().__init__(
            PluginMetadata(
                plugin_id="notion",
                name="Notion Integration",
                version="1.0.0",
                description="Read and append notes, project plans, and knowledge pages in Notion.",
                capabilities=["search_pages", "create_page", "append_block"],
            )
        )

    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "success",
            "plugin": "notion",
            "action": action,
            "message": f"Simulated Notion action '{action}' completed.",
        }


class WebhookPlugin(BasePlugin):
    """Dispatches webhooks and events to external URLs or services."""

    def __init__(self):
        super().__init__(
            PluginMetadata(
                plugin_id="webhook",
                name="Custom Webhooks",
                version="1.0.0",
                description="Broadcast events and task alerts to external HTTP webhooks.",
                capabilities=["post_event", "test_webhook"],
            )
        )

    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "success",
            "plugin": "webhook",
            "action": action,
            "payload_dispatched": params,
        }


class PluginManager:
    """Central registry and lifecycle manager for external integrations and plugins."""

    def __init__(self):
        self._plugins: Dict[str, BasePlugin] = {}
        self._register_default_plugins()

    def _register_default_plugins(self) -> None:
        self.register(GitHubPlugin())
        self.register(NotionPlugin())
        self.register(WebhookPlugin())

    def register(self, plugin: BasePlugin) -> None:
        """Register a new plugin instance."""
        self._plugins[plugin.plugin_id] = plugin

    def get_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        return self._plugins.get(plugin_id)

    def list_plugins(self) -> List[Dict[str, Any]]:
        """Return list of all registered plugins and their statuses."""
        return [
            {
                "id": p.plugin_id,
                "name": p.metadata.name,
                "version": p.metadata.version,
                "description": p.metadata.description,
                "enabled": p.is_enabled,
                "capabilities": p.metadata.capabilities,
            }
            for p in self._plugins.values()
        ]

    def set_plugin_status(self, plugin_id: str, enabled: bool) -> bool:
        """Enable or disable a plugin."""
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            return False
        if enabled:
            plugin.enable()
        else:
            plugin.disable()
        return True

    async def execute_plugin(
        self,
        plugin_id: str,
        action: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a capability on a registered plugin."""
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            return {"success": False, "error": f"Plugin '{plugin_id}' not found."}
        if not plugin.is_enabled:
            return {"success": False, "error": f"Plugin '{plugin_id}' is currently disabled."}

        try:
            res = await plugin.execute(action, params or {})
            return {"success": True, "result": res}
        except Exception as exc:
            return {"success": False, "error": str(exc)}


PLUGIN_MANAGER = PluginManager()
