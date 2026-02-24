from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from creativeai_studio.api.deps import AppContext
from creativeai_studio.api.assets import router as assets_router
from creativeai_studio.api.health import router as health_router
from creativeai_studio.api.jobs import router as jobs_router
from creativeai_studio.api.models import router as models_router
from creativeai_studio.api.settings import router as settings_router
from creativeai_studio.asset_store import AssetStore
from creativeai_studio.config import AppConfig
from creativeai_studio.db import Database
from creativeai_studio.repositories.assets_repo import AssetsRepo
from creativeai_studio.repositories.job_assets_repo import JobAssetsRepo
from creativeai_studio.repositories.jobs_repo import JobsRepo
from creativeai_studio.repositories.settings_repo import SettingsRepo
from creativeai_studio.providers.google_provider import GoogleProvider
from creativeai_studio.runner import JobRunner


def create_app(cfg: AppConfig | None = None) -> FastAPI:
    cfg = cfg or AppConfig.from_env()
    cfg.ensure_dirs()

    db = Database(cfg.db_path)
    db.init()

    ctx = AppContext(
        cfg=cfg,
        db=db,
        settings=SettingsRepo(db),
        assets=AssetsRepo(db),
        jobs=JobsRepo(db),
        job_assets=JobAssetsRepo(db),
        asset_store=AssetStore(cfg.data_dir),
    )

    try:
        from google import genai

        provider = GoogleProvider(client_factory=genai.Client, gcs=None)
    except Exception:  # noqa: BLE001
        provider = None

    runner = JobRunner(ctx, provider=provider, concurrency=1)

    @asynccontextmanager
    async def lifespan(app: FastAPI):  # noqa: ARG001
        runner.recover_on_startup()
        runner.start()
        yield

    app = FastAPI(title="CreativeAI-Studio API", lifespan=lifespan)
    app.state.ctx = ctx
    app.state.runner = runner

    app.include_router(health_router, prefix="/api")
    app.include_router(assets_router, prefix="/api")
    app.include_router(jobs_router, prefix="/api")
    app.include_router(models_router, prefix="/api")
    app.include_router(settings_router, prefix="/api")
    return app


app = create_app()
