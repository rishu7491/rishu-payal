"""Unified Multimodal Workflow Coordinator for Payal.

Integrates text, voice transcription, visual screenshot analysis, screen context,
and emotional speech synthesis into a unified execution loop.
"""

from dataclasses import dataclass, field
import time
from typing import Any, Dict, List, Optional

from .voice import VOICE_ENGINE, VoiceEngine
from .vision import VISION_ENGINE, VisionEngine
from .screen import SCREEN_MANAGER, ScreenContextManager


@dataclass
class MultimodalRequest:
    """Input payload containing one or more interaction modalities."""
    text: Optional[str] = None
    audio_bytes: Optional[bytes] = None
    image_data: Optional[bytes | str] = None
    capture_screen: bool = False
    context_notes: Optional[str] = None
    emotion: str = "neutral"
    execute_autonomously: bool = True


@dataclass
class MultimodalResponse:
    """Coordinated output across text, visual insights, execution results, and speech."""
    original_text: Optional[str] = None
    transcribed_text: Optional[str] = None
    vision_analysis: Optional[Dict[str, Any]] = None
    screen_context: Optional[Dict[str, Any]] = None
    orchestration_result: Optional[Dict[str, Any]] = None
    final_text: str = ""
    speech_output: Optional[Dict[str, Any]] = None
    emotion: str = "neutral"
    duration_seconds: float = 0.0
    success: bool = True
    error: Optional[str] = None


class MultimodalWorkflow:
    """Coordinates seamless interaction across voice, vision, screen, and text."""

    def __init__(
        self,
        voice_engine: Optional[VoiceEngine] = None,
        vision_engine: Optional[VisionEngine] = None,
        screen_manager: Optional[ScreenContextManager] = None,
        orchestrator=None,
    ):
        self.voice = voice_engine or VOICE_ENGINE
        self.vision = vision_engine or VISION_ENGINE
        self.screen = screen_manager or SCREEN_MANAGER
        self._orchestrator = orchestrator

    @property
    def orchestrator(self):
        if self._orchestrator is None:
            from core.orchestrator import UNIFIED_ORCHESTRATOR
            self._orchestrator = UNIFIED_ORCHESTRATOR
        return self._orchestrator

    async def process(self, request: MultimodalRequest) -> MultimodalResponse:
        """Execute the coordinated multimodal interaction pipeline."""
        start_time = time.time()
        transcribed_text = None
        vision_result = None
        screen_result = None
        orchestration_data = None
        error_msg = None

        try:
            # 1. Process Voice / Speech input if provided
            if request.audio_bytes:
                transcribed_text = await self.voice.transcribe_audio(request.audio_bytes)

            # 2. Process Image / Visual input if provided
            if request.image_data:
                vision_result = await self.vision.analyze_image(request.image_data)

            # 3. Process Screen Context if requested
            if request.capture_screen:
                screen_result = self.screen.capture_screen()
                if screen_result.get("success") and screen_result.get("path"):
                    screen_analysis = await self.vision.analyze_image(
                        screen_result["path"],
                        prompt="Analyze this active screen workspace context, active windows, and open files.",
                    )
                    screen_result["analysis"] = screen_analysis.get("analysis")

            # 4. Construct unified user goal / prompt
            components = []
            if request.text:
                components.append(f"User Request: {request.text}")
            if transcribed_text:
                components.append(f"Voice Transcription: {transcribed_text}")
            if vision_result and vision_result.get("analysis"):
                components.append(f"Attached Visual Context: {vision_result['analysis']}")
            if screen_result and screen_result.get("analysis"):
                win = screen_result.get("window_title", "Workspace")
                components.append(f"Current Screen Context [{win}]: {screen_result['analysis']}")
            if request.context_notes:
                components.append(f"Additional Context: {request.context_notes}")

            combined_goal = "\n\n".join(components).strip()
            if not combined_goal:
                combined_goal = "Status check and greeting."

            # 5. Route to Autonomous Orchestrator if execution requested
            final_text = ""
            if request.execute_autonomously:
                orch_res = await self.orchestrator.run(goal=combined_goal)
                orchestration_data = {
                    "goal": orch_res.goal,
                    "success": orch_res.success,
                    "final_output": orch_res.final_output,
                    "step_count": len(orch_res.step_results),
                    "duration": orch_res.total_duration_seconds,
                }
                final_text = orch_res.final_output or f"Completed goal: {combined_goal[:80]}"
            else:
                final_text = f"Multimodal context received and parsed successfully:\n{combined_goal}"

            # 6. Synthesize emotional voice response
            speech_info = await self.voice.synthesize_speech(
                text=final_text[:500],
                emotion=request.emotion,
            )

            duration = round(time.time() - start_time, 3)
            return MultimodalResponse(
                original_text=request.text,
                transcribed_text=transcribed_text,
                vision_analysis=vision_result,
                screen_context=screen_result,
                orchestration_result=orchestration_data,
                final_text=final_text,
                speech_output=speech_info,
                emotion=request.emotion,
                duration_seconds=duration,
                success=True,
            )

        except Exception as exc:
            duration = round(time.time() - start_time, 3)
            return MultimodalResponse(
                original_text=request.text,
                transcribed_text=transcribed_text,
                final_text=f"Encountered error during multimodal processing: {str(exc)}",
                emotion="serious",
                duration_seconds=duration,
                success=False,
                error=str(exc),
            )


MULTIMODAL_WORKFLOW = MultimodalWorkflow()
