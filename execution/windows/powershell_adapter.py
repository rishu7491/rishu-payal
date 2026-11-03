"""Payal AI - Windows PowerShell Execution Adapter.

Asynchronously and safely executes PowerShell commands on Windows 11.
"""

import asyncio
import os
import subprocess
from typing import Any, Dict, Optional


class PowerShellAdapter:

    def __init__(self, default_cwd: Optional[str] = None):
        self.default_cwd = default_cwd or os.getcwd()

    async def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: int = 60,
    ) -> Dict[str, Any]:
        """Execute a PowerShell command asynchronously with timeout."""
        target_cwd = cwd or self.default_cwd
        cmd = [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ]

        def _run():
            try:
                proc = subprocess.run(
                    cmd,
                    cwd=target_cwd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=False,
                )
                return {
                    "exit_code": proc.returncode,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "success": proc.returncode == 0,
                    "timed_out": False,
                }
            except subprocess.TimeoutExpired:
                return {
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": f"Command timed out after {timeout} seconds.",
                    "success": False,
                    "timed_out": True,
                }
            except Exception as e:
                return {
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": str(e),
                    "success": False,
                    "timed_out": False,
                }

        return await asyncio.to_thread(_run)


# Shared adapter instance
POWERSHELL = PowerShellAdapter()

