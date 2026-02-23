from __future__ import annotations

from typing import Any

from creativeai_studio.db import Database


class JobAssetsRepo:
    def __init__(self, db: Database):
        self._db = db

    def add(self, job_id: str, asset_id: str, role: str) -> None:
        with self._db.connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO job_assets(job_id, asset_id, role) VALUES(?, ?, ?)",
                (job_id, asset_id, role),
            )
            conn.commit()

    def list_by_job(self, job_id: str) -> list[dict[str, Any]]:
        with self._db.connect() as conn:
            rows = conn.execute(
                "SELECT job_id, asset_id, role FROM job_assets WHERE job_id = ? ORDER BY role, asset_id",
                (job_id,),
            ).fetchall()
        return [dict(r) for r in rows]

