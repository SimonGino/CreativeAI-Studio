from __future__ import annotations

from fastapi import FastAPI

from creativeai_studio.api.health import router as health_router
from creativeai_studio.config import AppConfig


def create_app(cfg: AppConfig | None = None) -> FastAPI:
    cfg = cfg or AppConfig.from_env()
    cfg.ensure_dirs()
    app = FastAPI(title="CreativeAI-Studio API")
    app.include_router(health_router, prefix="/api")
    return app


app = create_app()
