"""Ecosystem, Web, Vision, and Automation execution tools for Payal."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from .base import BaseTool
from .schemas import PermissionLevel, ToolCategory, ToolResult


class WebNavigateArgs(BaseModel):
    url: str = Field(..., description="The URL to visit")


class WebNavigateTool(BaseTool):
    """Tool to fetch and scrape content from web URLs."""
    name = "web_navigate"
    description = "Fetch, read, and extract readable text from a web URL."
    category = ToolCategory.BROWSER
    permission_level = PermissionLevel.LEVEL_1_READ_ONLY
    args_schema = WebNavigateArgs

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        from integrations.ecosystem import WEB_AUTOMATION
        url = arguments.get("url", "")
        res = await WEB_AUTOMATION.navigate(url)
        return ToolResult(
            success=res.success,
            data={"url": res.url, "title": res.title, "content": res.content_text},
            error=res.error,
        )


class ScreenCaptureArgs(BaseModel):
    pass


class ScreenCaptureTool(BaseTool):
    """Tool to capture active workspace screen context."""
    name = "screen_capture"
    description = "Capture a screenshot of current workspace with user permission."
    category = ToolCategory.SYSTEM
    permission_level = PermissionLevel.LEVEL_3_APPROVAL_REQUIRED
    args_schema = ScreenCaptureArgs

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        from core.multimodal import SCREEN_MANAGER
        res = SCREEN_MANAGER.capture_screen()
        return ToolResult(
            success=res.get("success", False),
            data=res,
            error=res.get("error"),
        )


class AnalyzeImageArgs(BaseModel):
    image_path: str = Field(..., description="Local path to image")
    prompt: str = Field(default="Analyze this image.", description="Analysis instructions")


class AnalyzeImageTool(BaseTool):
    """Tool to analyze an image, diagram, UI layout, or screenshot."""
    name = "analyze_image"
    description = "Inspect and reason about an image, screenshot, or diagram."
    category = ToolCategory.SYSTEM
    permission_level = PermissionLevel.LEVEL_1_READ_ONLY
    args_schema = AnalyzeImageArgs

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        from core.multimodal import VISION_ENGINE
        path = arguments.get("image_path", "")
        prompt = arguments.get("prompt", "Analyze this image.")
        res = await VISION_ENGINE.analyze_image(path, prompt=prompt)
        return ToolResult(
            success=res.get("success", True),
            data=res,
            error=res.get("error"),
        )


class CreateBackupArgs(BaseModel):
    tag: Optional[str] = Field(None, description="Optional tag name for backup")


class CreateBackupTool(BaseTool):
    """Tool to snapshot memory database and configurations."""
    name = "create_backup"
    description = "Create a snapshot backup of Payal's memory database and configs."
    category = ToolCategory.SYSTEM
    permission_level = PermissionLevel.LEVEL_2_WORKSPACE_REVERSIBLE
    args_schema = CreateBackupArgs

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        from core.monitoring import BACKUP_MANAGER
        tag = arguments.get("tag")
        res = BACKUP_MANAGER.create_backup(tag=tag)
        return ToolResult(
            success=res.get("success", True),
            data=res,
        )
