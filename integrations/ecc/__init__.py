"""ECC Integration Layer for Payal Core Engine.

Exports loaders, registry, models, and execution runners for all 314 Skills,
71 Agents, 22 Rule Suites, and 98 Commands/Workflows.
"""

from .loader import ECCLoader
from .models import (
    ECCAgent,
    ECCSkill,
    ECCRuleSuite,
    ECCCommand,
    ECCWorkflow,
    ComponentStats,
)
from .registry import ECCRegistry, ECC_REGISTRY
from .runner import (
    ECCRunner,
    ECC_RUNNER,
    AgentExecutionResult,
    SkillExecutionResult,
    CommandExecutionResult,
)

__all__ = [
    "ECCLoader",
    "ECCAgent",
    "ECCSkill",
    "ECCRuleSuite",
    "ECCCommand",
    "ECCWorkflow",
    "ComponentStats",
    "ECCRegistry",
    "ECC_REGISTRY",
    "ECCRunner",
    "ECC_RUNNER",
    "AgentExecutionResult",
    "SkillExecutionResult",
    "CommandExecutionResult",
]

