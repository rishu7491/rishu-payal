"""Multimodal Intelligence API routes for Payal."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from core.multimodal import (
    VOICE_ENGINE,
    VISION_ENGINE,
    SCREEN_MANAGER,
    MULTIMODAL_WORKFLOW,
    MultimodalRequest,
)

router = APIRouter(prefix="/api/multimodal", tags=["multimodal"])


class SynthesizeRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize into speech")
    emotion: str = Field(default="neutral", description="Assistant emotional tone")
    voice_id: Optional[str] = None


class VisionRequest(BaseModel):
    image_data: str = Field(..., description="Base64 encoded image string or file path")
    prompt: str = Field(
        default="Describe and analyze this image in detail.",
        description="Visual reasoning prompt",
    )
    mime_type: str = Field(default="image/png", description="Image MIME type")


class PermissionRequest(BaseModel):
    granted: bool = Field(..., description="Whether screen capture is allowed")


class WorkflowAPIRequest(BaseModel):
    text: Optional[str] = None
    image_data: Optional[str] = None
    capture_screen: bool = False
    context_notes: Optional[str] = None
    emotion: str = "neutral"
    execute_autonomously: bool = True


@router.post("/transcribe")
async def transcribe_audio_endpoint(
    file: Optional[UploadFile] = File(None),
    language: str = Form("hi"),
) -> Dict[str, Any]:
    """Transcribe spoken audio into text."""
    audio_bytes = b""
    filename = "input.wav"
    if file:
        audio_bytes = await file.read()
        filename = file.filename or filename

    text = await VOICE_ENGINE.transcribe_audio(
        audio_bytes=audio_bytes,
        filename=filename,
        language=language,
    )
    return {
        "status": "success",
        "transcribed_text": text,
        "language": language,
    }


@router.post("/synthesize")
async def synthesize_speech_endpoint(req: SynthesizeRequest) -> Dict[str, Any]:
    """Synthesize natural emotional voice parameters."""
    result = await VOICE_ENGINE.synthesize_speech(
        text=req.text,
        emotion=req.emotion,
        voice_id=req.voice_id,
    )
    return {"status": "success", "speech": result}


@router.post("/vision/analyze")
async def analyze_vision_endpoint(req: VisionRequest) -> Dict[str, Any]:
    """Analyze images, UI structures, or error screenshots."""
    res = await VISION_ENGINE.analyze_image(
        image_data=req.image_data,
        prompt=req.prompt,
        mime_type=req.mime_type,
    )
    return {"status": "success", "vision": res}


@router.get("/screen/status")
async def get_screen_status():
    """Get screen capture permission and active window title."""
    return {
        "permission_granted": SCREEN_MANAGER.has_permission,
        "active_window": SCREEN_MANAGER.get_active_window_title(),
    }


@router.post("/screen/permission")
async def set_screen_permission(req: PermissionRequest):
    """Grant or revoke screen observation permissions."""
    if req.granted:
        SCREEN_MANAGER.grant_permission()
    else:
        SCREEN_MANAGER.revoke_permission()
    return {
        "status": "success",
        "permission_granted": SCREEN_MANAGER.has_permission,
    }


@router.post("/screen/capture")
async def capture_screen_endpoint():
    """Capture current workspace screen."""
    res = SCREEN_MANAGER.capture_screen()
    if not res.get("success"):
        raise HTTPException(status_code=403, detail=res.get("error", "Capture failed"))
    return {"status": "success", "capture": res}


@router.post("/workflow")
async def run_multimodal_workflow_endpoint(req: WorkflowAPIRequest):
    """Execute end-to-end multimodal workflow combining text, vision, screen, and speech."""
    mm_req = MultimodalRequest(
        text=req.text,
        image_data=req.image_data,
        capture_screen=req.capture_screen,
        context_notes=req.context_notes,
        emotion=req.emotion,
        execute_autonomously=req.execute_autonomously,
    )
    res = await MULTIMODAL_WORKFLOW.process(mm_req)
    return {"status": "success" if res.success else "error", "result": res}
