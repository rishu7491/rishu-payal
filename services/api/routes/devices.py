"""Real-time Multi-Device Registry and Heartbeat API for Payal."""

from dataclasses import dataclass, field
import platform
import subprocess
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/devices", tags=["Devices"])


class DeviceHeartbeatRequest(BaseModel):
    device_id: str = Field(..., description="Unique device identifier (e.g., 'personal_phone', 'home_phone')")
    name: str = Field(..., description="Device display name")
    device_type: str = Field(default="android", description="'android', 'windows', 'linux'")
    battery: Optional[int] = Field(default=None, description="Battery percentage (0-100)")
    ip: Optional[str] = Field(default=None, description="Current local IP address")
    status: str = Field(default="online", description="Device status")


@dataclass
class DeviceNode:
    device_id: str
    name: str
    device_type: str
    role: str
    ip: str
    battery: Optional[int]
    online: bool
    last_seen: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class DeviceRegistry:
    def __init__(self):
        self.devices: Dict[str, DeviceNode] = {
            "windows_laptop": DeviceNode(
                device_id="windows_laptop",
                name="Windows Laptop",
                device_type="windows",
                role="Primary Core Engine Host",
                ip="10.196.121.14:8000",
                battery=100,
                online=True,
                last_seen=time.time(),
                metadata={"os": f"{platform.system()} {platform.release()}"},
            ),
            "personal_phone": DeviceNode(
                device_id="personal_phone",
                name="Personal Phone",
                device_type="android",
                role="Portable Voice Assistant & Floating Orb",
                ip="10.196.121.182",
                battery=100,
                online=False,
                last_seen=0.0,
                metadata={"model": "Samsung Galaxy A50s"},
            ),
            "home_phone": DeviceNode(
                device_id="home_phone",
                name="Home Phone",
                device_type="android",
                role="Stationary Room Voice Terminal",
                ip="Waiting for registration",
                battery=None,
                online=False,
                last_seen=0.0,
                metadata={},
            ),
        }

    def update_heartbeat(self, req: DeviceHeartbeatRequest) -> DeviceNode:
        node = self.devices.get(req.device_id)
        if not node:
            node = DeviceNode(
                device_id=req.device_id,
                name=req.name,
                device_type=req.device_type,
                role="Connected Mesh Node",
                ip=req.ip or "Unknown",
                battery=req.battery,
                online=True,
                last_seen=time.time(),
            )
            self.devices[req.device_id] = node
        else:
            node.name = req.name
            node.online = True
            node.last_seen = time.time()
            if req.battery is not None:
                node.battery = req.battery
            if req.ip:
                node.ip = req.ip
        return node

    def refresh_states(self):
        now = time.time()
        # Windows host is always online while API responds
        if "windows_laptop" in self.devices:
            self.devices["windows_laptop"].last_seen = now
            self.devices["windows_laptop"].online = True

        # Check ADB connected devices for personal phone
        adb_connected = self._check_adb_connected()
        if "personal_phone" in self.devices:
            if adb_connected or (now - self.devices["personal_phone"].last_seen < 90):
                self.devices["personal_phone"].online = True
                self.devices["personal_phone"].last_seen = now
            else:
                self.devices["personal_phone"].online = False

        # Home phone check
        if "home_phone" in self.devices:
            if now - self.devices["home_phone"].last_seen < 90:
                self.devices["home_phone"].online = True
            else:
                self.devices["home_phone"].online = False

    def _check_adb_connected(self) -> bool:
        adb_path = r"C:\Users\risha\AppData\Local\Android\Sdk\platform-tools\adb.exe"
        try:
            res = subprocess.run([adb_path, "devices"], capture_output=True, text=True, timeout=2)
            for line in res.stdout.splitlines():
                if "\tdevice" in line or " device " in line:
                    return True
        except Exception:
            pass
        return False


DEVICE_REGISTRY = DeviceRegistry()


@router.get("")
async def list_devices() -> Dict[str, Any]:
    """Return live status of all registered mesh devices."""
    DEVICE_REGISTRY.refresh_states()
    devices_list = []
    for d in DEVICE_REGISTRY.devices.values():
        devices_list.append({
            "device_id": d.device_id,
            "name": d.name,
            "device_type": d.device_type,
            "role": d.role,
            "ip": d.ip,
            "battery": d.battery,
            "online": d.online,
            "last_seen_seconds_ago": int(time.time() - d.last_seen) if d.last_seen > 0 else None,
            "metadata": d.metadata,
        })
    online_count = sum(1 for d in devices_list if d["online"])
    return {
        "status": "success",
        "online_count": online_count,
        "total_count": len(devices_list),
        "devices": devices_list,
    }


@router.post("/heartbeat")
async def device_heartbeat(req: DeviceHeartbeatRequest):
    """Register or refresh heartbeat from a phone or mesh client."""
    node = DEVICE_REGISTRY.update_heartbeat(req)
    return {"status": "ok", "device_id": node.device_id, "online": True}

