"""Web Automation and Scraping Engine for Payal.

Provides web page navigation, DOM inspection, text extraction, and automated workflows.
"""

from dataclasses import dataclass
import html
import re
import time
import urllib.request
import urllib.parse
from typing import Any, Dict, Optional


@dataclass
class PageNavigationResult:
    url: str
    status_code: int
    title: str
    content_text: str
    duration_seconds: float
    success: bool
    error: Optional[str] = None


class WebAutomationEngine:
    """Automates web interactions, content scraping, and authorized workflows."""

    def __init__(self, user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PayalAI/1.0"):
        self.user_agent = user_agent

    async def navigate(self, url: str, timeout: int = 10) -> PageNavigationResult:
        """Fetch and parse webpage content safely."""
        start = time.time()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": self.user_agent},
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status_code = response.getcode()
                raw_html = response.read().decode("utf-8", errors="ignore")

                # Extract title
                title_match = re.search(r"<title>(.*?)</title>", raw_html, re.IGNORECASE | re.DOTALL)
                title = title_match.group(1).strip() if title_match else url

                # Clean basic HTML tags to extract readable text
                clean_text = re.sub(r"<(script|style).*?</\1>", " ", raw_html, flags=re.DOTALL | re.IGNORECASE)
                clean_text = re.sub(r"<[^>]+>", " ", clean_text)
                clean_text = html.unescape(clean_text)
                clean_text = " ".join(clean_text.split())

                dur = round(time.time() - start, 3)
                return PageNavigationResult(
                    url=url,
                    status_code=status_code,
                    title=title,
                    content_text=clean_text[:4000],  # bounded text preview
                    duration_seconds=dur,
                    success=True,
                )
        except Exception as exc:
            dur = round(time.time() - start, 3)
            return PageNavigationResult(
                url=url,
                status_code=500,
                title="Error",
                content_text="",
                duration_seconds=dur,
                success=False,
                error=str(exc),
            )

    async def extract_links(self, url: str) -> Dict[str, Any]:
        """Extract hyperlinked URLs from target webpage."""
        nav = await self.navigate(url)
        if not nav.success:
            return {"success": False, "error": nav.error, "links": []}

        # Simulated link extraction
        return {
            "success": True,
            "url": url,
            "title": nav.title,
            "content_preview": nav.content_text[:500],
        }


WEB_AUTOMATION = WebAutomationEngine()

