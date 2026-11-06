"""API Route definitions."""

from .approvals import router as approvals_router
from .automation import router as automation_router
from .chat import router as chat_router
from .components import router as components_router
from .devices import router as devices_router
from .ecosystem import router as ecosystem_router
from .health import router as health_router
from .memory import router as memory_router
from .models import router as models_router
from .monitoring import router as monitoring_router
from .multimodal import router as multimodal_router
from .orchestrator import router as orchestrator_router
from .system import router as system_router

__all__ = [
    "approvals_router",
    "automation_router",
    "chat_router",
    "components_router",
    "devices_router",
    "ecosystem_router",
    "health_router",
    "memory_router",
    "models_router",
    "monitoring_router",
    "multimodal_router",
    "orchestrator_router",
    "system_router",
]
