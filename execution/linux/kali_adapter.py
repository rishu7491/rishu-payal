"""Payal AI - Kali Linux Integration Adapter.

Provides seamless command execution and tool interaction with Kali Linux via:
1. Oracle VirtualBox VM ('kali-linux-2026.3-virtualbox-amd64')
2. Windows Subsystem for Linux (WSL Kali)
"""

import asyncio
import os
import subprocess
from typing import Any, Dict
from core.identity.config import CONFIG


class KaliAdapter:

    def __init__(self, config=None):
        self.config = config or CONFIG.kali

    def _run_cmd(self, cmd_args, timeout=30):
        try:
            res = subprocess.run(
                cmd_args,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            return {
                "exit_code": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "success": res.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s",
                "success": False,
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "success": False,
            }

    def get_status(self) -> Dict[str, Any]:
        """Check status of VirtualBox Kali VM and WSL."""
        status = {
            "virtualbox_installed": os.path.exists(
                self.config.vbox_manage_path
            ),
            "vm_registered": False,
            "vm_running": False,
            "wsl_available": False,
            "preferred_mode": "none",
        }

        # 1. VirtualBox check
        if status["virtualbox_installed"]:
            vbox = self.config.vbox_manage_path
            # Check registered VMs
            res = self._run_cmd([vbox, "list", "vms"], timeout=5)
            if self.config.vm_name in res.get("stdout", ""):
                status["vm_registered"] = True

            # Check running VMs
            res_running = self._run_cmd([vbox, "list", "runningvms"], timeout=5)
            if self.config.vm_name in res_running.get("stdout", ""):
                status["vm_running"] = True

        # 2. WSL check
        res_wsl = self._run_cmd(["wsl", "-l", "-q"], timeout=5)
        if res_wsl.get("success"):
            status["wsl_available"] = True
            distros = res_wsl.get("stdout", "")
            if self.config.wsl_distro in distros:
                status["wsl_kali_installed"] = True
            else:
                status["wsl_kali_installed"] = False

        if status["vm_running"] or status["vm_registered"]:
            status["preferred_mode"] = "virtualbox"
        elif status.get("wsl_kali_installed"):
            status["preferred_mode"] = "wsl"
        elif status["wsl_available"]:
            status["preferred_mode"] = "wsl_generic"

        return status

    def start_virtualbox_vm(self, headless: bool = True) -> Dict[str, Any]:
        """Start the VirtualBox Kali VM."""
        if not os.path.exists(self.config.vbox_manage_path):
            return {
                "success": False,
                "error": "VirtualBox VBoxManage.exe not found",
            }

        vbox = self.config.vbox_manage_path
        vm_type = "headless" if headless else "gui"
        cmd = [vbox, "startvm", self.config.vm_name, "--type", vm_type]
        res = self._run_cmd(cmd, timeout=30)
        return res

    def execute_wsl(self, command: str, timeout: int = 60) -> Dict[str, Any]:
        """Execute a command in Kali / Linux via WSL."""
        distro = self.config.wsl_distro
        cmd = ["wsl", "-d", distro, "--", "bash", "-c", command]
        res = self._run_cmd(cmd, timeout=timeout)
        if not res["success"] and "not found" in res.get("stderr", "").lower():
            # Fall back to default WSL instance if specific kali distro isn't set up yet
            cmd_fallback = ["wsl", "--", "bash", "-c", command]
            return self._run_cmd(cmd_fallback, timeout=timeout)
        return res

    def execute_vbox_guest(
        self, command: str, timeout: int = 60
    ) -> Dict[str, Any]:
        """Execute a command in the VirtualBox VM via VBoxManage guestcontrol."""
        vbox = self.config.vbox_manage_path
        cmd = [
            vbox,
            "guestcontrol",
            self.config.vm_name,
            "run",
            "--username",
            self.config.guest_user,
            "--password",
            self.config.guest_password,
            "--exe",
            "/bin/bash",
            "--",
            "/bin/bash",
            "-c",
            command,
        ]
        return self._run_cmd(cmd, timeout=timeout)

    async def execute(
        self, command: str, timeout: int = 60
    ) -> Dict[str, Any]:
        """Execute command in Kali using the best available mode."""
        st = self.get_status()

        if st["vm_running"]:
            return await asyncio.to_thread(
                self.execute_vbox_guest, command, timeout
            )
        elif st.get("wsl_kali_installed") or st["wsl_available"]:
            return await asyncio.to_thread(self.execute_wsl, command, timeout)
        elif st["vm_registered"]:
            # VM registered but not running
            return {
                "success": False,
                "error": f"Kali VM '{self.config.vm_name}' is registered in VirtualBox but currently stopped. Call start_kali_vm() to boot it.",
                "exit_code": -1,
            }
        else:
            return {
                "success": False,
                "error": "Neither VirtualBox Kali VM nor WSL is ready to execute commands.",
                "exit_code": -1,
            }


# Shared adapter instance
KALI = KaliAdapter()

