"""Unit tests for Phase 7 Voice and Multimodal Intelligence."""

import asyncio
import pytest
from core.multimodal import (
    VOICE_ENGINE,
    VISION_ENGINE,
    SCREEN_MANAGER,
    MULTIMODAL_WORKFLOW,
    MultimodalRequest,
)


def test_voice_engine():
    params_happy = VOICE_ENGINE.get_speech_parameters("happy")
    assert params_happy["pitch"] > 1.0

    params_sad = VOICE_ENGINE.get_speech_parameters("sad")
    assert params_sad["pitch"] < 1.0

    async def run_async():
        transcription = await VOICE_ENGINE.transcribe_audio(b"dummy_wav_bytes")
        assert "Transcribed" in transcription

        speech_out = await VOICE_ENGINE.synthesize_speech("Hello Payal", emotion="proud")
        assert speech_out["emotion"] == "proud"
        assert "parameters" in speech_out

    asyncio.run(run_async())


def test_vision_engine():
    async def run_async():
        res = await VISION_ENGINE.analyze_image(
            b"mock_image_bytes",
            prompt="Identify components in this diagram",
        )
        assert res["success"] is True
        assert "Visual Analysis" in res["analysis"] or res["provider"] != ""

        elements = await VISION_ENGINE.detect_ui_elements(b"mock_image_bytes")
        assert isinstance(elements, list)
        assert len(elements) > 0

    asyncio.run(run_async())


def test_screen_context_manager():
    # Verify permission gating
    SCREEN_MANAGER.revoke_permission()
    assert SCREEN_MANAGER.has_permission is False
    blocked_capture = SCREEN_MANAGER.capture_screen()
    assert blocked_capture["success"] is False
    assert "permission" in blocked_capture["error"].lower()

    # Grant permission and capture
    SCREEN_MANAGER.grant_permission()
    assert SCREEN_MANAGER.has_permission is True
    capture = SCREEN_MANAGER.capture_screen()
    assert capture["success"] is True
    assert "path" in capture


def test_multimodal_workflow():
    async def run_async():
        req = MultimodalRequest(
            text="Check system status and report",
            audio_bytes=b"sample_voice",
            emotion="excited",
            execute_autonomously=False,
        )
        resp = await MULTIMODAL_WORKFLOW.process(req)
        assert resp.success is True
        assert resp.transcribed_text is not None
        assert resp.speech_output is not None
        assert resp.duration_seconds >= 0.0

    asyncio.run(run_async())
