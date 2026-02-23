from __future__ import annotations

from fastapi import FastAPI

from creativeai_studio.api.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="CreativeAI-Studio API")
    app.include_router(health_router, prefix="/api")
    return app


app = create_app()
