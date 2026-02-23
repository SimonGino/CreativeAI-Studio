from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from creativeai_studio.db import Database


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _row_to_job(row: Any) -> dict[str, Any]:
    d = dict(row)
    d["params"] = json.loads(d.pop("params_json") or "{}")
    if d.get("result_json") is not None:
        d["result"] = json.loads(d.pop("result_json") or "null")
    else:
        d.pop("result_json", None)
        d["result"] = None
    return d


class JobsRepo:
    def __init__(self, db: Database):
        self._db = db

    def create(
        self,
        job_id: str,
        job_type: str,
        model_id: str,
        auth_mode: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        created_at = _now_iso()
        with self._db.connect() as conn:
            conn.execute(
                """
                INSERT INTO jobs(
                  id, job_type, model_id, auth_mode,
                  status, cancel_requested, progress, status_message,
                  params_json, result_json,
                  error_message, error_detail,
                  created_at, started_at, finished_at
                )
                VALUES(?, ?, ?, ?, 'queued', 0, NULL, NULL, ?, NULL, NULL, NULL, ?, NULL, NULL)
                """,
                (job_id, job_type, model_id, auth_mode, _json_dumps(params), created_at),
            )
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            conn.commit()
        assert row is not None
        return _row_to_job(row)

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._db.connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if row is None:
            return None
        return _row_to_job(row)

    def list(
        self,
        status: str | None = None,
        job_type: str | None = None,
        model_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        where = []
        params: list[Any] = []

        if status is not None:
            where.append("status = ?")
            params.append(status)
        if job_type is not None:
            where.append("job_type = ?")
            params.append(job_type)
        if model_id is not None:
            where.append("model_id = ?")
            params.append(model_id)

        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        params.extend([limit, offset])

        with self._db.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM jobs
                {where_sql}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                params,
            ).fetchall()

        return [_row_to_job(r) for r in rows]

    def set_status(self, job_id: str, status: str, status_message: str | None = None) -> None:
        started_at = _now_iso() if status == "running" else None
        with self._db.connect() as conn:
            if started_at is None:
                conn.execute(
                    "UPDATE jobs SET status = ?, status_message = ? WHERE id = ?",
                    (status, status_message, job_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE jobs
                    SET status = ?, status_message = ?, started_at = COALESCE(started_at, ?)
                    WHERE id = ?
                    """,
                    (status, status_message, started_at, job_id),
                )
            conn.commit()

    def set_succeeded(self, job_id: str, result_dict: dict[str, Any]) -> None:
        now = _now_iso()
        with self._db.connect() as conn:
            conn.execute(
                """
                UPDATE jobs
                SET status = 'succeeded',
                    status_message = NULL,
                    result_json = ?,
                    error_message = NULL,
                    error_detail = NULL,
                    started_at = COALESCE(started_at, ?),
                    finished_at = ?
                WHERE id = ?
                """,
                (_json_dumps(result_dict), now, now, job_id),
            )
            conn.commit()

    def set_failed(self, job_id: str, message: str, detail: Any | None = None) -> None:
        now = _now_iso()
        error_detail = None if detail is None else (detail if isinstance(detail, str) else _json_dumps(detail))
        with self._db.connect() as conn:
            conn.execute(
                """
                UPDATE jobs
                SET status = 'failed',
                    status_message = NULL,
                    result_json = NULL,
                    error_message = ?,
                    error_detail = ?,
                    started_at = COALESCE(started_at, ?),
                    finished_at = ?
                WHERE id = ?
                """,
                (message, error_detail, now, now, job_id),
            )
            conn.commit()

    def request_cancel(self, job_id: str) -> None:
        with self._db.connect() as conn:
            conn.execute(
                "UPDATE jobs SET cancel_requested = 1 WHERE id = ?",
                (job_id,),
            )
            conn.commit()

