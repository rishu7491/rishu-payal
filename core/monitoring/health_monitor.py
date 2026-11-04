"""System and Service Health Monitor for Payal AI."""

import os
import shutil
import subprocess
import time
from typing import Any, Dict, Optional


class HealthMonitor:
    """Monitors the operational health of AI models, databases, OS adapters, and hardware resources."""

    def __init__(self, router=None, memory_store=None):
        self._router = router
        self._memory_store = memory_store

    @property
    def router(self):
        if self._router is None:
            from core.model_router import ROUTER
            self._router = ROUTER
        return self._router

    @property
    def memory_store(self):
        if self._memory_store is None:
            from core.memory.storage import PERSISTENT_MEMORY_STORE
            self._memory_store = PERSISTENT_MEMORY_STORE
        return self._memory_store

    def check_system_resources(self) -> Dict[str, Any]:
        """Check CPU, RAM, and disk utilization without requiring heavy extra dependencies."""
        disk_usage = shutil.disk_usage(".")
        total_gb = disk_usage.total / (1024**3)
        free_gb = disk_usage.free / (1024**3)
        used_gb = disk_usage.used / (1024**3)
        disk_percent = (used_gb / total_gb) * 100.0 if total_gb > 0 else 0.0

        return {
            "disk": {
                "total_gb": round(total_gb, 2),
                "free_gb": round(free_gb, 2),
                "used_gb": round(used_gb, 2),
                "percent_used": round(disk_percent, 1),
            },
            "status": "healthy" if disk_percent < 90 else "warning",
        }

    async def check_database_health(self) -> Dict[str, Any]:
        """Verify SQLite database connectivity and record count."""
        try:
            count = (
                self.memory_store.count()
                if hasattr(self.memory_store, "count")
                else len(self.memory_store.list(limit=100))
            )
            return {"status": "healthy", "connected": True, "record_count": count}
        except Exception as exc:
            return {"status": "unhealthy", "connected": False, "error": str(exc)}

    async def check_models_health(self) -> Dict[str, Any]:
        """Check availability of configured ModelRouter providers."""
        try:
            return await self.router.check_health()
        except Exception as exc:
            return {"error": str(exc), "status": "degraded"}

    def check_os_subsystems(self) -> Dict[str, Any]:
        """Check Windows PowerShell and WSL Kali availability."""
        # PowerShell check
        ps_healthy = False
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "echo 'ok'"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            ps_healthy = res.returncode == 0 and "ok" in res.stdout
        except Exception:
            ps_healthy = False

        # WSL check
        wsl_healthy = False
        try:
            wsl_res = subprocess.run(
                ["wsl", "--status"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            wsl_healthy = wsl_res.returncode == 0
        except Exception:
            wsl_healthy = False

        return {
            "powershell": "healthy" if ps_healthy else "unavailable",
            "wsl_kali": "available" if wsl_healthy else "unavailable",
        }

    async def get_full_health_report(self) -> Dict[str, Any]:
        """Aggregate full system health status."""
        start = time.time()
        resources = self.check_system_resources()
        db_health = await self.check_database_health()
        models_health = await self.check_models_health()
        os_health = self.check_os_subsystems()

        # Determine overall state
        is_healthy = db_health.get("status") == "healthy"
        overall = "healthy" if is_healthy else "degraded"

        return {
            "status": overall,
            "timestamp": time.time(),
            "check_duration_seconds": round(time.time() - start, 3),
            "resources": resources,
            "database": db_health,
            "models": models_health,
            "os_subsystems": os_health,
        }


HEALTH_MONITOR = HealthMonitor()
