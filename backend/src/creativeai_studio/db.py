from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assets (
  id TEXT PRIMARY KEY,
  media_type TEXT NOT NULL,            -- image|video
  origin TEXT NOT NULL,                -- upload|generated
  file_path TEXT NOT NULL,             -- relative to DATA_DIR
  mime_type TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,
  width INTEGER,
  height INTEGER,
  duration_seconds REAL,
  parent_asset_id TEXT,
  source_job_id TEXT,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  job_type TEXT NOT NULL,              -- image.generate|video.generate|video.extend
  model_id TEXT NOT NULL,
  auth_mode TEXT NOT NULL,             -- api_key|vertex
  status TEXT NOT NULL,                -- queued|running|succeeded|failed|canceled
  cancel_requested INTEGER NOT NULL DEFAULT 0,
  progress REAL,
  status_message TEXT,
  params_json TEXT NOT NULL,
  result_json TEXT,
  error_message TEXT,
  error_detail TEXT,
  created_at TEXT NOT NULL,
  started_at TEXT,
  finished_at TEXT
);

CREATE TABLE IF NOT EXISTS job_assets (
  job_id TEXT NOT NULL,
  asset_id TEXT NOT NULL,
  role TEXT NOT NULL,                  -- input_reference|input_start|input_end|input_video|output
  PRIMARY KEY(job_id, asset_id, role)
);
"""


@dataclass(frozen=True)
class Database:
    path: Path

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()
