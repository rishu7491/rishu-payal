"""API routes for System Tasks (Windows 11 / Kali Linux) and Emotion Tagging."""

import re
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from execution.windows.powershell_adapter import PowerShellAdapter
from execution.linux.kali_adapter import KALI, KaliAdapter

router = APIRouter(prefix="/api/system", tags=["System & Emotion"])

powershell = PowerShellAdapter()


class CommandExecRequest(BaseModel):
    system: str = Field(default="windows", description="'windows' (PowerShell) or 'kali' (Kali Linux / WSL)")
    command: str = Field(..., description="Command string to execute")
    cwd: Optional[str] = Field(default=None, description="Working directory")
    timeout: int = Field(default=60, ge=1, le=300)


class EmotionClassifyRequest(BaseModel):
    text: str = Field(..., description="Assistant text to analyze and tag with emotion")


@router.post("/exec")
async def execute_command(req: CommandExecRequest):
    """Execute a command on Windows 11 PowerShell or Kali Linux."""
    try:
        if req.system.lower() == "kali":
            res = await KALI.execute(req.command, timeout=req.timeout)
            return {
                "system": "kali",
                "success": res.get("success", False),
                "stdout": res.get("stdout", ""),
                "stderr": res.get("stderr", "") or res.get("error", ""),
                "exit_code": res.get("exit_code", 0 if res.get("success") else 1),
            }
        else:
            res = await powershell.execute(req.command, cwd=req.cwd, timeout=req.timeout)
            return {
                "system": "windows",
                "success": res.get("success", False),
                "stdout": res.get("stdout", ""),
                "stderr": res.get("stderr", ""),
                "exit_code": res.get("exit_code", 0 if res.get("success") else 1),
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_system_status():
    """Retrieve operational status for Windows host and Kali Linux integration."""
    import platform
    kali_st = KALI.get_status()
    return {
        "host_os": f"{platform.system()} {platform.release()}",
        "architecture": platform.machine(),
        "kali": kali_st,
    }


@router.post("/emotion")
async def classify_emotion(req: EmotionClassifyRequest):
    """Classify emotion and modulate voice parameters (pitch, rate, intensity)."""
    text = req.text.lower()

    # Rule-based sentiment & keyword matching with Hindi/Hinglish & English support
    happy_keywords = ["congratulations", "badhiya", "shabash", "mubarak", "great", "excellent", "done", "complete", "khushi", "good job", "proud of you"]
    proud_keywords = ["milestone", "victory", "champion", "achieved", "target met", "proud", "workout complete", "bca complete"]
    excited_keywords = ["awesome", "amazing", "wow", "zabardast", "fantastic", "let's go", "chalo shuru", "super", "ready!"]
    sad_keywords = ["failed", "error", "missed", "chhoot gaya", "incomplete", "regret", "sorry", "afsos", "warning", "fail"]
    serious_keywords = ["security", "critical", "caution", "strict", "attention", "urgent", "must", "danger", "rule", "protocol"]
    thinking_keywords = ["analyzing", "calculating", "searching", "soch", "processing", "planning", "verifying", "checking"]

    emotion = "neutral"
    intensity = 0.6
    pitch = 1.0
    rate = 1.0

    if any(k in text for k in proud_keywords):
        emotion = "proud"
        intensity = 0.95
        pitch = 1.15
        rate = 1.05
    elif any(k in text for k in excited_keywords):
        emotion = "excited"
        intensity = 0.9
        pitch = 1.25
        rate = 1.15
    elif any(k in text for k in happy_keywords):
        emotion = "happy"
        intensity = 0.85
        pitch = 1.15
        rate = 1.05
    elif any(k in text for k in sad_keywords):
        emotion = "sad"
        intensity = 0.75
        pitch = 0.85
        rate = 0.85
    elif any(k in text for k in serious_keywords):
        emotion = "serious"
        intensity = 0.85
        pitch = 0.95
        rate = 0.95
    elif any(k in text for k in thinking_keywords):
        emotion = "thinking"
        intensity = 0.7
        pitch = 1.0
        rate = 0.95

    return {
        "text": req.text,
        "emotion": emotion,
        "intensity": intensity,
        "pitch": pitch,
        "rate": rate,
    }

