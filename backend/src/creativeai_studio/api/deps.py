from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request

from creativeai_studio.asset_store import AssetStore
from creativeai_studio.config import AppConfig
from creativeai_studio.db import Database
from creativeai_studio.repositories.assets_repo import AssetsRepo
from creativeai_studio.repositories.job_assets_repo import JobAssetsRepo
from creativeai_studio.repositories.jobs_repo import JobsRepo
from creativeai_studio.repositories.settings_repo import SettingsRepo


@dataclass(frozen=True)
class AppContext:
    cfg: AppConfig
    db: Database
    settings: SettingsRepo
    assets: AssetsRepo
    jobs: JobsRepo
    job_assets: JobAssetsRepo
    asset_store: AssetStore


def get_ctx(request: Request) -> AppContext:
    return request.app.state.ctx

