"""Chat completion endpoint for Payal Core Engine."""

import re
from fastapi import APIRouter, Depends, HTTPException
from core.identity.config import CONFIG
from core.identity.persona import SYSTEM_PROMPT
from core.model_router.router import ROUTER, ModelRouter
from core.model_router.schemas import ChatMessage, CompletionRequest
from services.api.schemas import ChatRequest, ChatResponse


def clean_conversational_text(text: str) -> str:
    """Strip out system-level technical disclaimers, skipped lines, or internal boilerplates."""
    if not text:
        return ""
    # Strip *Skipped: ...* and *Risk: ...*
    cleaned = re.sub(r"\n*---*\s*\*Skipped:.*?(?:\n|$)", "", text, flags=re.DOTALL).strip()
    cleaned = re.sub(r"\*Skipped:[^\*]*\*", "", cleaned, flags=re.DOTALL).strip()
    cleaned = re.sub(r"\*Risk:[^\*]*\*", "", cleaned, flags=re.DOTALL).strip()
    return cleaned.strip()


router = APIRouter(prefix="/api/v1", tags=["Chat"])


def get_model_router() -> ModelRouter:
    """Dependency for obtaining the shared ModelRouter singleton."""
    return ROUTER


@router.post("/chat", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest,
    router_instance: ModelRouter = Depends(get_model_router),
):
    """Execute chat completion using Payal's Model Router with fallback support."""
    if not request.messages:
        raise HTTPException(
            status_code=400,
            detail="Chat request 'messages' cannot be empty.",
        )

    prepared_messages = list(request.messages)

    # Inject Payal's independent system prompt if none is present
    has_system = any(m.role == "system" for m in prepared_messages)
    if request.include_system_prompt and not has_system:
        prepared_messages.insert(
            0,
            ChatMessage(role="system", content=SYSTEM_PROMPT),
        )

    completion_req = CompletionRequest(
        messages=prepared_messages,
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        timeout_seconds=request.timeout_seconds,
        session_id=request.session_id,
    )

    try:
        response = await router_instance.generate(
            completion_req,
            provider_name=request.provider,
        )
        return ChatResponse(
            content=clean_conversational_text(response.content),
            model=response.model,
            provider=response.provider,
            session_id=response.session_id,
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except RuntimeError as err:
        raise HTTPException(status_code=502, detail=str(err))
    except Exception as err:
        raise HTTPException(
            status_code=500,
            detail=f"Internal chat completion error: {err}",
        )

