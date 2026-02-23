from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from creativeai_studio.db import Database


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _row_to_asset(row: Any) -> dict[str, Any]:
    d = dict(row)
    d["metadata"] = json.loads(d.pop("metadata_json") or "{}")
    return d


class AssetsRepo:
    def __init__(self, db: Database):
        self._db = db

    def insert_upload(
        self,
        asset_id: str,
        media_type: str,
        file_path: str,
        mime_type: str,
        size_bytes: int,
        width: int | None = None,
        height: int | None = None,
        duration_seconds: float | None = None,
    ) -> dict[str, Any]:
        created_at = _now_iso()
        with self._db.connect() as conn:
            conn.execute(
                """
                INSERT INTO assets(
                  id, media_type, origin, file_path, mime_type, size_bytes,
                  width, height, duration_seconds,
                  parent_asset_id, source_job_id,
                  metadata_json, created_at
                )
                VALUES(?, ?, 'upload', ?, ?, ?, ?, ?, ?, NULL, NULL, '{}', ?)
                """,
                (
                    asset_id,
                    media_type,
                    file_path,
                    mime_type,
                    size_bytes,
                    width,
                    height,
                    duration_seconds,
                    created_at,
                ),
            )
            row = conn.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
            conn.commit()
        assert row is not None
        return _row_to_asset(row)

    def insert_generated(
        self,
        asset_id: str,
        media_type: str,
        file_path: str,
        mime_type: str,
        size_bytes: int,
        source_job_id: str,
        parent_asset_id: str | None = None,
        width: int | None = None,
        height: int | None = None,
        duration_seconds: float | None = None,
    ) -> dict[str, Any]:
        created_at = _now_iso()
        with self._db.connect() as conn:
            conn.execute(
                """
                INSERT INTO assets(
                  id, media_type, origin, file_path, mime_type, size_bytes,
                  width, height, duration_seconds,
                  parent_asset_id, source_job_id,
                  metadata_json, created_at
                )
                VALUES(?, ?, 'generated', ?, ?, ?, ?, ?, ?, ?, ?, '{}', ?)
                """,
                (
                    asset_id,
                    media_type,
                    file_path,
                    mime_type,
                    size_bytes,
                    width,
                    height,
                    duration_seconds,
                    parent_asset_id,
                    source_job_id,
                    created_at,
                ),
            )
            row = conn.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
            conn.commit()
        assert row is not None
        return _row_to_asset(row)

    def get(self, asset_id: str) -> dict[str, Any] | None:
        with self._db.connect() as conn:
            row = conn.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if row is None:
            return None
        return _row_to_asset(row)

    def list(
        self,
        media_type: str | None = None,
        origin: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        where = []
        params: list[Any] = []

        if media_type is not None:
            where.append("media_type = ?")
            params.append(media_type)
        if origin is not None:
            where.append("origin = ?")
            params.append(origin)

        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        params.extend([limit, offset])

        with self._db.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM assets
                {where_sql}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                params,
            ).fetchall()

        return [_row_to_asset(r) for r in rows]

