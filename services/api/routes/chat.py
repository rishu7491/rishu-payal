"""Chat completion endpoint for Payal Core Engine."""

from fastapi import APIRouter, Depends, HTTPException
from core.identity.config import CONFIG
from core.identity.persona import SYSTEM_PROMPT
from core.model_router.router import ModelRouter
from core.model_router.schemas import ChatMessage, CompletionRequest
from services.api.schemas import ChatRequest, ChatResponse


router = APIRouter(prefix="/api/v1", tags=["Chat"])


def get_model_router() -> ModelRouter:
    """Dependency for obtaining the ModelRouter instance."""
    return ModelRouter(config=CONFIG)


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
            content=response.content,
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

