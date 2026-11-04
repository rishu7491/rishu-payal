"""Payal Core Engine FastAPI Application."""

from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from core.identity.config import CONFIG
from core.identity.identity import get_identity
from services.api.routes import (
    automation_router,
    chat_router,
    components_router,
    ecosystem_router,
    health_router,
    memory_router,
    models_router,
    monitoring_router,
    multimodal_router,
    orchestrator_router,
    system_router,
)


def create_app() -> FastAPI:
    """Factory creating and configuring the Payal FastAPI instance."""
    identity = get_identity()

    app = FastAPI(
        title=f"{identity.name} Core Engine API",
        description=f"{identity.title} - Owned by {identity.owner}",
        version=CONFIG.config_version,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Cross-Origin Resource Sharing
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Standardized validation error handler
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "type": "validation_error",
                    "message": "Invalid request parameters",
                    "details": exc.errors(),
                }
            },
        )

    # Include route modules
    app.include_router(health_router)
    app.include_router(models_router)
    app.include_router(chat_router)
    app.include_router(components_router)
    app.include_router(orchestrator_router)
    app.include_router(memory_router)
    app.include_router(system_router)
    app.include_router(automation_router)
    app.include_router(multimodal_router)
    app.include_router(monitoring_router)
    app.include_router(ecosystem_router)

    # Mount Static Web Interface for Desktop & Mobile UI
    frontend_dir = Path(__file__).resolve().parent.parent.parent / "apps" / "frontend"
    if frontend_dir.exists():
        app.mount("/ui", StaticFiles(directory=str(frontend_dir), html=True), name="ui")
        app.mount("/app", StaticFiles(directory=str(frontend_dir), html=True), name="app")

    @app.get("/")
    async def root():
        return {
            "platform": identity.name,
            "owner": identity.owner,
            "title": identity.title,
            "version": CONFIG.config_version,
            "status": "operational",
            "ui": "/ui",
            "app": "/app",
            "docs": "/docs",
        }

    return app


app = create_app()

