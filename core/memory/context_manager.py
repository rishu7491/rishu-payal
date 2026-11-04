"""Harness Engineering Tiered Context Manager for Payal Core Engine.

Maintains active task context in structured L0, L1, L2 tiers,
preventing context rot and token saturation during autonomous runs.
"""

import time
from typing import Dict, List, Optional

from .models import ContextTiers


class ContextManager:
    """Manages active task memory with L0 (Abstract), L1 (Overview), and L2 (Detail) tiers."""

    def __init__(self, max_tokens_estimate: int = 4000):
        self.tiers = ContextTiers()
        self.max_tokens_estimate = max_tokens_estimate
        self._l2_entries: List[str] = []

    def set_l0(self, goal: str, constraints: Optional[List[str]] = None) -> None:
        """L0 Tier: Milestone goals, operational constraints, identity."""
        constraint_str = "\n".join(f"- {c}" for c in (constraints or []))
        self.tiers.l0_abstract = (
            f"### [L0 - Abstract Goal & Constraints]\n"
            f"**Current Goal:** {goal}\n"
            f"**Constraints:**\n{constraint_str if constraint_str else 'Standard safety and harness guardrails.'}"
        )
        self.tiers.updated_at = time.time()

    def set_l1(
        self,
        architecture: Optional[str] = None,
        plan_summary: Optional[str] = None,
        components: Optional[List[str]] = None,
    ) -> None:
        """L1 Tier: Architecture, API contracts, active phase checklist, components."""
        parts = ["### [L1 - Architecture & Overview]"]
        if plan_summary:
            parts.append(f"**Active Plan:** {plan_summary}")
        if architecture:
            parts.append(f"**Architecture:** {architecture}")
        if components:
            parts.append(f"**Components:** {', '.join(components)}")

        self.tiers.l1_overview = "\n".join(parts)
        self.tiers.updated_at = time.time()

    def append_l2(self, detail_type: str, content: str) -> None:
        """L2 Tier: Specific function signatures, error traces, or tool outputs."""
        # Truncate large individual outputs to prevent blowup (e.g., max 1500 chars per entry)
        clipped = content[:1500] + ("\n...[truncated]" if len(content) > 1500 else "")
        entry = f"**[{detail_type}]**\n{clipped}"
        self._l2_entries.append(entry)

        # Keep only the last 6 recent detail entries to prevent context rot
        if len(self._l2_entries) > 6:
            self._l2_entries = self._l2_entries[-6:]

        self.tiers.l2_detail = "### [L2 - Active Execution Details]\n" + "\n\n".join(self._l2_entries)
        self.tiers.updated_at = time.time()

    def build_context(self) -> str:
        """Assemble tiered context into a coherent, high-signal prompt string."""
        sections: List[str] = []
        if self.tiers.l0_abstract:
            sections.append(self.tiers.l0_abstract)
        if self.tiers.l1_overview:
            sections.append(self.tiers.l1_overview)
        if self.tiers.l2_detail:
            sections.append(self.tiers.l2_detail)

        full_context = "\n\n".join(sections)
        # Approximate 1 token ~= 4 chars
        char_limit = self.max_tokens_estimate * 4
        if len(full_context) > char_limit:
            full_context = full_context[:char_limit] + "\n...[Context truncated by budget]"
        return full_context

    def clear(self) -> None:
        """Reset all active tiers for a new execution session."""
        self.tiers = ContextTiers()
        self._l2_entries = []


# Global singleton context manager
CONTEXT_MANAGER = ContextManager()

