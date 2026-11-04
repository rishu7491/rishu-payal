"""Payal Core Engine FastAPI Application."""

from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from core.identity.config import CONFIG
from core.identity.identity import get_identity
from services.api.routes import chat, components, health, memory, models, orchestrator, system


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
    app.include_router(health.router)
    app.include_router(models.router)
    app.include_router(chat.router)
    app.include_router(components.router)
    app.include_router(orchestrator.router)
    app.include_router(memory.router)
    app.include_router(system.router)

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

