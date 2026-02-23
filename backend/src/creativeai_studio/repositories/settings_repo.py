from __future__ import annotations

import json
from typing import Any

from creativeai_studio.db import Database


class SettingsRepo:
    def __init__(self, db: Database):
        self._db = db

    def set_json(self, key: str, value: Any) -> None:
        value_json = json.dumps(value, ensure_ascii=False)
        with self._db.connect() as conn:
            conn.execute(
                """
                INSERT INTO settings(key, value_json)
                VALUES(?, ?)
                ON CONFLICT(key) DO UPDATE SET value_json = excluded.value_json
                """,
                (key, value_json),
            )
            conn.commit()

    def get_json(self, key: str, default: Any | None = None) -> Any:
        with self._db.connect() as conn:
            row = conn.execute(
                "SELECT value_json FROM settings WHERE key = ?",
                (key,),
            ).fetchone()
        if row is None:
            return default
        return json.loads(row["value_json"])

    def set_str(self, key: str, value: str) -> None:
        self.set_json(key, value)

    def get_str(self, key: str, default: str | None = None) -> str | None:
        value = self.get_json(key, default=default)
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError(f"Expected setting '{key}' to be str, got {type(value).__name__}")
        return value

