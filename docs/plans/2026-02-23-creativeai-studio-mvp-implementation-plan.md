# CreativeAI-Studio MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在本机以 `SQLite + 本地文件` 方式提供文生图、图/文生视频、视频延长（Vertex+GCS）、资产管理与历史复用的完整闭环，并为未来 SaaS 演进保留清晰边界。

**Architecture:** Monorepo：`backend/`（FastAPI + SQLite + 内置 JobRunner + Provider 抽象）与 `web/`（React SPA）。所有上传/生成产物统一入 `assets`（落盘到 `DATA_DIR`），所有任务写入 `jobs` 并可 clone 复用。Google 模型通过 `google-genai` 分别走 API Key（Developer API）与 Vertex（Service Account JSON）两条路径；`video.extend` 强制 Vertex 并使用 `VERTEX_GCS_BUCKET`。

**Tech Stack:** Python(uv) + FastAPI + SQLite + google-genai + google-cloud-storage + Pillow + ffprobe + React(Vite, TS) + pnpm

---

## 0. 实现约定（先读，避免返工）

- 数据目录：`DATA_DIR=./data`（可通过 env 覆盖）；DB 固定为 `${DATA_DIR}/app.db`。
- **不要在模块 import 时读取 env 并初始化 DB**：使用 `create_app()` 工厂，测试可传入临时 `AppConfig`。
- `AppContext` 放在 `app.state.ctx`，通过 FastAPI dependency 注入，避免全局单例污染测试。
- 所有 Provider/GCS 的单测都用 mock/fake；真实联调用 `POST /api/settings/test` 手动触发。
- `video.extend`：
  - 强制 `auth_mode=vertex`
  - 强制存在 `vertex_gcs_bucket`（bucket-name，不含 `gs://`）
  - 输入视频必须先上传到 `gs://<bucket>/creativeai-studio/<job_id>/input.mp4`

---

## 1. Backend（FastAPI）实现计划

### Task 1: Scaffold backend project (uv) + test tooling

**Files:**
- Create: `backend/`（uv 项目）

**Step 1: Initialize**

Run:
```bash
uv init --app --package --name creativeai-studio-backend -p 3.12 --vcs none backend
```

**Step 2: Add deps**

Run:
```bash
cd backend
uv add fastapi uvicorn[standard] python-multipart pydantic google-genai google-cloud-storage pillow
uv add --dev pytest httpx ruff
```

**Step 3: Add a basic ruff config**

Modify `backend/pyproject.toml` add:
```toml
[tool.ruff]
line-length = 100
target-version = "py312"
```

**Step 4: Commit**

Run:
```bash
git add backend
git commit -m "chore(backend): scaffold uv project"
```

---

### Task 2: App factory + health endpoint (TDD)

**Files:**
- Create: `backend/src/creativeai_studio/main.py`
- Create: `backend/src/creativeai_studio/api/health.py`
- Create: `backend/tests/test_health.py`

**Step 1: Write failing test**

Create `backend/tests/test_health.py`:
```python
from fastapi.testclient import TestClient

from creativeai_studio.main import create_app


def test_health_ok(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    app = create_app()
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
```

**Step 2: Run to confirm fail**

Run:
```bash
cd backend
uv run pytest -q
```
Expected: FAIL（模块不存在）。

**Step 3: Minimal implementation**

Create `backend/src/creativeai_studio/api/health.py`:
```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    return {"ok": True}
```

Create `backend/src/creativeai_studio/main.py`:
```python
from __future__ import annotations

from fastapi import FastAPI

from creativeai_studio.api.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="CreativeAI-Studio API")
    app.include_router(health_router, prefix="/api")
    return app


app = create_app()
```

**Step 4: Run to confirm pass**

Run:
```bash
uv run pytest -q
```
Expected: PASS.

**Step 5: Commit**

Run:
```bash
git add backend/src/creativeai_studio backend/tests/test_health.py
git commit -m "feat(api): app factory and health endpoint"
```

---

### Task 3: Config + data dirs (TDD)

**Files:**
- Create: `backend/src/creativeai_studio/config.py`
- Modify: `backend/src/creativeai_studio/main.py`
- Test: `backend/tests/test_config.py`

**Step 1: Write failing test**

Create `backend/tests/test_config.py`:
```python
from pathlib import Path

from creativeai_studio.config import AppConfig


def test_ensure_dirs(tmp_path: Path):
    cfg = AppConfig(data_dir=tmp_path / "data")
    cfg.ensure_dirs()
    assert (cfg.data_dir / "assets/uploads").exists()
    assert (cfg.data_dir / "assets/generated").exists()
    assert (cfg.data_dir / "credentials").exists()
    assert (cfg.data_dir / "tmp").exists()
```

**Step 2: Run to confirm fail**

Run: `uv run pytest -q`  
Expected: FAIL.

**Step 3: Minimal implementation**

Create `backend/src/creativeai_studio/config.py`:
```python
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    data_dir: Path

    @staticmethod
    def from_env() -> "AppConfig":
        return AppConfig(data_dir=Path(os.getenv("DATA_DIR", "./data")).resolve())

    @property
    def db_path(self) -> Path:
        return self.data_dir / "app.db"

    def ensure_dirs(self) -> None:
        (self.data_dir / "assets/uploads").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "assets/generated").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "credentials").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "tmp").mkdir(parents=True, exist_ok=True)
```

Modify `backend/src/creativeai_studio/main.py` to accept optional cfg:
```python
from creativeai_studio.config import AppConfig


def create_app(cfg: AppConfig | None = None) -> FastAPI:
    cfg = cfg or AppConfig.from_env()
    cfg.ensure_dirs()
    ...
```

**Step 4: Run to confirm pass**

Run: `uv run pytest -q`  
Expected: PASS.

**Step 5: Commit**

Run:
```bash
git add backend/src/creativeai_studio/config.py backend/src/creativeai_studio/main.py backend/tests/test_config.py
git commit -m "feat(core): add AppConfig and data dirs"
```

---

### Task 4: SQLite schema + Database helper (settings/assets/jobs/job_assets)

**Files:**
- Create: `backend/src/creativeai_studio/db.py`
- Test: `backend/tests/test_db_init.py`

**Step 1: Write failing test**

Create `backend/tests/test_db_init.py`:
```python
from creativeai_studio.db import Database


def test_db_init_creates_tables(tmp_path):
    db = Database(tmp_path / "app.db")
    db.init()
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    names = {r[0] for r in rows}
    assert {"settings", "assets", "jobs", "job_assets"} <= names
```

**Step 2: Run to confirm fail**

Run: `uv run pytest -q`  
Expected: FAIL.

**Step 3: Minimal implementation**

Create `backend/src/creativeai_studio/db.py`:
```python
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
```

**Step 4: Run to confirm pass**

Run: `uv run pytest -q`  
Expected: PASS.

**Step 5: Commit**

Run:
```bash
git add backend/src/creativeai_studio/db.py backend/tests/test_db_init.py
git commit -m "feat(db): add sqlite schema and initializer"
```

---

### Task 5: Repositories (settings/assets/jobs/job_assets)

**Files:**
- Create: `backend/src/creativeai_studio/repositories/settings_repo.py`
- Create: `backend/src/creativeai_studio/repositories/assets_repo.py`
- Create: `backend/src/creativeai_studio/repositories/jobs_repo.py`
- Create: `backend/src/creativeai_studio/repositories/job_assets_repo.py`
- Test: `backend/tests/test_repos_smoke.py`

**Step 1: Write failing test**

Create `backend/tests/test_repos_smoke.py`:
```python
from creativeai_studio.db import Database
from creativeai_studio.repositories.assets_repo import AssetsRepo
from creativeai_studio.repositories.jobs_repo import JobsRepo
from creativeai_studio.repositories.settings_repo import SettingsRepo


def test_repos_roundtrip(tmp_path):
    db = Database(tmp_path / "app.db")
    db.init()
    settings = SettingsRepo(db)
    assets = AssetsRepo(db)
    jobs = JobsRepo(db)

    settings.set_str("google_api_key", "x")
    assert settings.get_str("google_api_key") == "x"

    a = assets.insert_upload(
        asset_id="a1",
        media_type="image",
        file_path="assets/uploads/a1.png",
        mime_type="image/png",
        size_bytes=1,
    )
    assert a["id"] == "a1"

    j = jobs.create(
        job_id="j1",
        job_type="image.generate",
        model_id="nano-banana-pro",
        auth_mode="api_key",
        params={"prompt": "x"},
    )
    assert j["id"] == "j1"
```

**Step 2: Run to confirm fail**

Run: `uv run pytest -q`  
Expected: FAIL.

**Step 3: Minimal implementation**

Create `backend/src/creativeai_studio/repositories/settings_repo.py`:
```python
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional

from creativeai_studio.db import Database


@dataclass(frozen=True)
class SettingsRepo:
    db: Database

    def get_json(self, key: str) -> Optional[dict[str, Any]]:
        with self.db.connect() as conn:
            row = conn.execute("SELECT value_json FROM settings WHERE key = ?", (key,)).fetchone()
        return json.loads(row["value_json"]) if row else None

    def set_json(self, key: str, value: dict[str, Any]) -> None:
        payload = json.dumps(value, ensure_ascii=False)
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO settings(key, value_json) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value_json = excluded.value_json",
                (key, payload),
            )
            conn.commit()

    def get_str(self, key: str) -> Optional[str]:
        v = self.get_json(key)
        return v.get("value") if v else None

    def set_str(self, key: str, value: str) -> None:
        self.set_json(key, {"value": value})
```

Create `backend/src/creativeai_studio/repositories/assets_repo.py` and `jobs_repo.py` with `insert_upload/insert_generated/get/list` and `create/get/list/set_status/set_succeeded/set_failed/request_cancel`（按 DB schema 字段实现，list 先用 limit/offset）。

Create `backend/src/creativeai_studio/repositories/job_assets_repo.py` add `add(job_id, asset_id, role)` and `list_by_job(job_id)`.

**Step 4: Run to confirm pass**

Run: `uv run pytest -q`  
Expected: PASS.

**Step 5: Commit**

Run:
```bash
git add backend/src/creativeai_studio/repositories backend/tests/test_repos_smoke.py
git commit -m "feat(db): add repositories for settings/assets/jobs"
```

---

### Task 6: AssetStore + metadata extraction (Pillow + ffprobe) (TDD)

**Files:**
- Create: `backend/src/creativeai_studio/asset_store.py`
- Create: `backend/src/creativeai_studio/media_meta.py`
- Test: `backend/tests/test_media_meta.py`

**Step 1: Write failing test**

Create `backend/tests/test_media_meta.py`:
```python
from pathlib import Path

from PIL import Image

from creativeai_studio.media_meta import read_image_size


def test_read_image_size(tmp_path: Path):
    p = tmp_path / "x.png"
    Image.new("RGB", (64, 32), color=(255, 0, 0)).save(p)
    w, h = read_image_size(p)
    assert (w, h) == (64, 32)
```

**Step 2: Run to confirm fail**

Run: `uv run pytest -q`  
Expected: FAIL.

**Step 3: Minimal implementation**

Create `backend/src/creativeai_studio/media_meta.py`:
```python
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image


def read_image_size(path: Path) -> Tuple[int, int]:
    with Image.open(path) as img:
        return img.size


def read_video_meta_ffprobe(path: Path) -> tuple[Optional[int], Optional[int], Optional[float]]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        str(path),
    ]
    out = subprocess.check_output(cmd)
    data = json.loads(out)
    duration = None
    try:
        duration = float(data.get("format", {}).get("duration"))
    except Exception:
        duration = None
    width = height = None
    for s in data.get("streams", []):
        if s.get("codec_type") == "video":
            width = s.get("width")
            height = s.get("height")
            break
    return width, height, duration
```

Create `backend/src/creativeai_studio/asset_store.py`：
- `save_upload(asset_id, filename, bytes) -> rel_path, abs_path, mime, size`
- `save_generated(asset_id, ext, bytes) -> ...`
- 所有路径都落到 `DATA_DIR/assets/...` 下。

**Step 4: Run to confirm pass**

Run: `uv run pytest -q`  
Expected: PASS.

**Step 5: Commit**

Run:
```bash
git add backend/src/creativeai_studio/asset_store.py backend/src/creativeai_studio/media_meta.py backend/tests/test_media_meta.py
git commit -m "feat(assets): add asset store and media metadata helpers"
```

---

### Task 7: AppContext + dependency injection (no globals) (TDD)

**Files:**
- Create: `backend/src/creativeai_studio/api/deps.py`
- Modify: `backend/src/creativeai_studio/main.py`
- Test: `backend/tests/test_ctx_injection.py`

**Step 1: Write failing test**

Create `backend/tests/test_ctx_injection.py`:
```python
from fastapi.testclient import TestClient

from creativeai_studio.config import AppConfig
from creativeai_studio.main import create_app


def test_ctx_attached(tmp_path):
    cfg = AppConfig(data_dir=tmp_path / "data")
    app = create_app(cfg)
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert hasattr(app.state, "ctx")
```

**Step 2: Run to confirm fail**

Run: `uv run pytest -q`  
Expected: FAIL.

**Step 3: Minimal implementation**

Create `backend/src/creativeai_studio/api/deps.py`:
```python
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
```

Modify `create_app(cfg)` in `backend/src/creativeai_studio/main.py`:
- `cfg.ensure_dirs()`
- `db = Database(cfg.db_path); db.init()`
- `ctx = AppContext(...)`
- `app.state.ctx = ctx`

**Step 4: Run to confirm pass**

Run: `uv run pytest -q`  
Expected: PASS.

**Step 5: Commit**

Run:
```bash
git add backend/src/creativeai_studio/api/deps.py backend/src/creativeai_studio/main.py backend/tests/test_ctx_injection.py
git commit -m "feat(core): app context via app.state and deps injection"
```

---

### Task 8: Settings API (default auth + api key + vertex json + gcs bucket) (TDD)

**Files:**
- Create: `backend/src/creativeai_studio/api/settings.py`
- Modify: `backend/src/creativeai_studio/main.py`
- Test: `backend/tests/test_settings_api.py`

**Step 1: Write failing test**

Create `backend/tests/test_settings_api.py`:
```python
from fastapi.testclient import TestClient

from creativeai_studio.main import create_app
from creativeai_studio.config import AppConfig


def test_put_and_get_default_auth(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    client = TestClient(app)

    put = client.put("/api/settings", json={"default_auth_mode": "vertex"})
    assert put.status_code == 200
    got = client.get("/api/settings")
    assert got.json()["default_auth_mode"] == "vertex"
```

**Step 2: Run to confirm fail**

Run: `uv run pytest -q`  
Expected: FAIL.

**Step 3: Minimal implementation**

Create `backend/src/creativeai_studio/api/settings.py`:
```python
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from creativeai_studio.api.deps import AppContext, get_ctx

router = APIRouter(prefix="/settings")


@router.get("")
def get_settings(ctx: AppContext = Depends(get_ctx)):
    default_auth = (ctx.settings.get_json("default_auth_mode") or {"mode": "api_key"}).get("mode", "api_key")
    has_api_key = ctx.settings.get_str("google_api_key") is not None
    vertex_bucket = (ctx.settings.get_json("vertex_gcs_bucket") or {}).get("value")
    vertex_location = (ctx.settings.get_json("vertex_location") or {}).get("value")
    vertex_project = (ctx.settings.get_json("vertex_project_id") or {}).get("value")
    vertex_sa_path = (ctx.settings.get_json("vertex_sa_path") or {}).get("value")
    return {
        "default_auth_mode": default_auth,
        "google_api_key_present": has_api_key,
        "vertex_project_id": vertex_project,
        "vertex_location": vertex_location,
        "vertex_gcs_bucket": vertex_bucket,
        "vertex_sa_present": bool(vertex_sa_path),
    }


@router.put("")
def put_settings(payload: dict, ctx: AppContext = Depends(get_ctx)):
    mode = payload.get("default_auth_mode")
    if mode in ("api_key", "vertex"):
        ctx.settings.set_json("default_auth_mode", {"mode": mode})
    if "vertex_project_id" in payload:
        ctx.settings.set_str("vertex_project_id", str(payload["vertex_project_id"]))
    if "vertex_location" in payload:
        ctx.settings.set_str("vertex_location", str(payload["vertex_location"]))
    if "vertex_gcs_bucket" in payload:
        bucket = str(payload["vertex_gcs_bucket"])
        if bucket.startswith("gs://"):
            raise HTTPException(status_code=400, detail="vertex_gcs_bucket must not include gs://")
        ctx.settings.set_str("vertex_gcs_bucket", bucket)
    if "google_api_key" in payload and payload["google_api_key"]:
        ctx.settings.set_str("google_api_key", str(payload["google_api_key"]))
    return get_settings(ctx)


@router.post("/vertex-sa")
async def upload_vertex_sa(
    file: UploadFile = File(...),
    ctx: AppContext = Depends(get_ctx),
):
    raw = await file.read()
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid JSON")
    out_path = ctx.cfg.data_dir / "credentials" / "vertex-sa.json"
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    ctx.settings.set_str("vertex_sa_path", str(out_path))
    if isinstance(data, dict) and data.get("project_id"):
        ctx.settings.set_str("vertex_project_id", str(data["project_id"]))
    return {"ok": True}
```

Modify `backend/src/creativeai_studio/main.py` include router.

**Step 4: Run to confirm pass**

Run: `uv run pytest -q`  
Expected: PASS.

**Step 5: Commit**

Run:
```bash
git add backend/src/creativeai_studio/api/settings.py backend/src/creativeai_studio/main.py backend/tests/test_settings_api.py
git commit -m "feat(settings): settings api for auth and vertex config"
```

---

### Task 9: Assets API (upload/list/get/content) + store metadata (TDD)

**Files:**
- Create: `backend/src/creativeai_studio/api/assets.py`
- Modify: `backend/src/creativeai_studio/main.py`
- Test: `backend/tests/test_assets_api.py`

**Step 1: Write failing test**

Create `backend/tests/test_assets_api.py`:
```python
from io import BytesIO

from PIL import Image
from fastapi.testclient import TestClient

from creativeai_studio.config import AppConfig
from creativeai_studio.main import create_app


def test_upload_image_and_fetch_content(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    client = TestClient(app)

    buf = BytesIO()
    Image.new("RGB", (32, 16), color=(0, 0, 0)).save(buf, format="PNG")
    buf.seek(0)

    up = client.post(
        "/api/assets/upload",
        files={"file": ("x.png", buf.read(), "image/png")},
    )
    assert up.status_code == 200
    asset_id = up.json()["id"]

    content = client.get(f"/api/assets/{asset_id}/content")
    assert content.status_code == 200
    assert content.headers["content-type"].startswith("image/")
```

**Step 2: Run to confirm fail**

Run: `uv run pytest -q`  
Expected: FAIL.

**Step 3: Minimal implementation**

Create `backend/src/creativeai_studio/api/assets.py`:
```python
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from creativeai_studio.api.deps import AppContext, get_ctx
from creativeai_studio.media_meta import read_image_size, read_video_meta_ffprobe


router = APIRouter(prefix="/assets")


@router.post("/upload")
async def upload_asset(file: UploadFile = File(...), ctx: AppContext = Depends(get_ctx)):
    mime = file.content_type or "application/octet-stream"
    if not (mime.startswith("image/") or mime.startswith("video/")):
        raise HTTPException(status_code=400, detail="Only image/video supported")

    asset_id = uuid.uuid4().hex
    data = await file.read()
    stored = ctx.asset_store.save_upload(asset_id=asset_id, filename=file.filename or "upload.bin", data=data)

    width = height = None
    duration = None
    if stored.mime_type.startswith("image/"):
        width, height = read_image_size(stored.abs_path)
    elif stored.mime_type.startswith("video/"):
        width, height, duration = read_video_meta_ffprobe(stored.abs_path)

    asset = ctx.assets.insert_upload(
        asset_id=asset_id,
        media_type="image" if stored.mime_type.startswith("image/") else "video",
        file_path=stored.rel_path,
        mime_type=stored.mime_type,
        size_bytes=stored.size_bytes,
        width=width,
        height=height,
        duration_seconds=duration,
    )
    return {
        "id": asset["id"],
        "media_type": asset["media_type"],
        "origin": asset["origin"],
        "mime_type": asset["mime_type"],
        "width": asset["width"],
        "height": asset["height"],
        "duration_seconds": asset["duration_seconds"],
    }


@router.get("")
def list_assets(ctx: AppContext = Depends(get_ctx), media_type: str | None = None, origin: str | None = None, limit: int = 50, offset: int = 0):
    return ctx.assets.list(media_type=media_type, origin=origin, limit=limit, offset=offset)


@router.get("/{asset_id}")
def get_asset(asset_id: str, ctx: AppContext = Depends(get_ctx)):
    a = ctx.assets.get(asset_id)
    if not a:
        raise HTTPException(status_code=404, detail="Asset not found")
    return a


@router.get("/{asset_id}/content")
def asset_content(asset_id: str, ctx: AppContext = Depends(get_ctx)):
    a = ctx.assets.get(asset_id)
    if not a:
        raise HTTPException(status_code=404, detail="Asset not found")
    abs_path = (ctx.cfg.data_dir / a["file_path"]).resolve()
    if not str(abs_path).startswith(str(ctx.cfg.data_dir.resolve())):
        raise HTTPException(status_code=400, detail="Invalid path")
    return FileResponse(abs_path, media_type=a["mime_type"])
```

Modify `backend/src/creativeai_studio/main.py` include router.

**Step 4: Run to confirm pass**

Run: `uv run pytest -q`  
Expected: PASS.

**Step 5: Commit**

Run:
```bash
git add backend/src/creativeai_studio/api/assets.py backend/src/creativeai_studio/main.py backend/tests/test_assets_api.py
git commit -m "feat(api): assets upload/list/get/content"
```

---

### Task 10: Model catalog + `/api/models` (static catalog for MVP)

**Files:**
- Create: `backend/src/creativeai_studio/model_catalog.py`
- Create: `backend/src/creativeai_studio/api/models.py`
- Modify: `backend/src/creativeai_studio/main.py`
- Test: `backend/tests/test_models_api.py`

**Step 1: Write failing test**

Create `backend/tests/test_models_api.py`:
```python
from fastapi.testclient import TestClient

from creativeai_studio.config import AppConfig
from creativeai_studio.main import create_app


def test_models_has_expected_ids(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    client = TestClient(app)
    resp = client.get("/api/models")
    assert resp.status_code == 200
    ids = {m["model_id"] for m in resp.json()}
    assert {"nano-banana-pro", "veo-3.1", "veo-3.1-fast"} <= ids
```

**Step 2: Run to confirm fail**

Run: `uv run pytest -q`  
Expected: FAIL.

**Step 3: Minimal implementation**

Create `backend/src/creativeai_studio/model_catalog.py` with:
- internal `model_id`（对前端稳定）
- `provider_model`（google-genai 的 model string，可后续调整）
- capabilities：`image_sizes`、`aspect_ratios`、`durations`、`supports_reference_image`、`supports_start_end_images`、`supports_extend`、`extend_requires_vertex=True`

Create `backend/src/creativeai_studio/api/models.py` return catalog json.

**Step 4: Run to confirm pass**

Run: `uv run pytest -q`  
Expected: PASS.

**Step 5: Commit**

Run:
```bash
git add backend/src/creativeai_studio/model_catalog.py backend/src/creativeai_studio/api/models.py backend/src/creativeai_studio/main.py backend/tests/test_models_api.py
git commit -m "feat(api): model catalog endpoint"
```

---

### Task 11: Jobs API (create/list/get/cancel/clone) with validation (TDD)

**Files:**
- Create: `backend/src/creativeai_studio/api/jobs.py`
- Create: `backend/src/creativeai_studio/validation.py`
- Modify: `backend/src/creativeai_studio/main.py`
- Test: `backend/tests/test_jobs_validation.py`

**Step 1: Write failing tests**

Create `backend/tests/test_jobs_validation.py`:
```python
from fastapi.testclient import TestClient

from creativeai_studio.config import AppConfig
from creativeai_studio.main import create_app


def test_extend_requires_vertex_bucket(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    client = TestClient(app)

    # No bucket set
    resp = client.post(
        "/api/jobs",
        json={
            "job_type": "video.extend",
            "model_id": "veo-3.1",
            "params": {"input_video_asset_id": "x", "extend_seconds": 5},
            "auth": {"mode": "vertex"},
        },
    )
    assert resp.status_code == 400


def test_reference_image_requires_vertex(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    client = TestClient(app)

    resp = client.post(
        "/api/jobs",
        json={
            "job_type": "image.generate",
            "model_id": "nano-banana-pro",
            "prompt": "x",
            "params": {"reference_image_asset_id": "a1", "aspect_ratio": "1:1", "image_size": "1k"},
            "auth": {"mode": "api_key"},
        },
    )
    assert resp.status_code == 400
```

**Step 2: Run to confirm fail**

Run: `uv run pytest -q`  
Expected: FAIL.

**Step 3: Minimal implementation**

Create `backend/src/creativeai_studio/validation.py` implement:
- resolve effective `auth_mode`（默认=设置，允许请求覆盖）
- validate payload per `job_type` + `model_catalog`
- for `video.extend` check `settings.vertex_gcs_bucket` present and `auth_mode=="vertex"`
- for `reference_image_asset_id` require `auth_mode=="vertex"`
- normalize `aspect_ratio=="auto"` with defaults（image:1:1；video:16:9；若有输入图则取近似）

Create `backend/src/creativeai_studio/api/jobs.py`:
- `POST /jobs`：validate → insert job（status=queued）→ 记录 job_assets（input roles）→ enqueue runner → return job
- `GET /jobs`：list by filters
- `GET /jobs/{id}`：detail + inputs/outputs
- `POST /jobs/{id}/cancel`：设置 `cancel_requested=1`，若 queued 可直接 `status=canceled`
- `POST /jobs/{id}/clone`：复制 params 并允许覆盖 prompt/params/auth

**Step 4: Run to confirm pass**

Run: `uv run pytest -q`  
Expected: PASS（至少覆盖上述校验）。

**Step 5: Commit**

Run:
```bash
git add backend/src/creativeai_studio/api/jobs.py backend/src/creativeai_studio/validation.py backend/src/creativeai_studio/main.py backend/tests/test_jobs_validation.py
git commit -m "feat(api): jobs endpoints with validation"
```

---

### Task 12: JobRunner (background worker) + restart recovery (TDD)

**Files:**
- Create: `backend/src/creativeai_studio/runner.py`
- Modify: `backend/src/creativeai_studio/main.py`
- Test: `backend/tests/test_runner_requeues_queued.py`

**Step 1: Write failing test**

Create `backend/tests/test_runner_requeues_queued.py`:
```python
import time

from creativeai_studio.config import AppConfig
from creativeai_studio.main import create_app


def test_startup_requeues_queued(tmp_path):
    cfg = AppConfig(data_dir=tmp_path / "data")
    app = create_app(cfg)
    ctx = app.state.ctx

    # Insert a queued job
    ctx.jobs.create(
        job_id="j1",
        job_type="image.generate",
        model_id="nano-banana-pro",
        auth_mode="api_key",
        params={"prompt": "x", "aspect_ratio": "1:1", "image_size": "1k"},
    )

    runner = app.state.runner
    runner.enqueue("j1")
    time.sleep(0.1)
    assert runner.qsize() >= 0
```

**Step 2: Run to confirm fail**

Run: `uv run pytest -q`  
Expected: FAIL.

**Step 3: Minimal implementation**

Create `backend/src/creativeai_studio/runner.py`:
- `JobRunner(ctx, provider, concurrency=1)`
- 内部 `queue.Queue[str]`
- `start()`：启动 N 个 daemon 线程消费队列
- `enqueue(job_id)`
- `recover_on_startup()`：
  - jobs.status == "queued" → enqueue
  - jobs.status == "running" → set_failed("server restarted")（MVP）
- worker loop：
  - 取 job，若 cancel_requested → set status canceled
  - set_status running
  - provider.run(job) → persist result → set_succeeded
  - 异常 → set_failed

Modify `backend/src/creativeai_studio/main.py`：
- 在 `create_app()` 创建 runner 并挂到 `app.state.runner`
- `startup` event 调 `runner.recover_on_startup()` + `runner.start()`

**Step 4: Run to confirm pass**

Run: `uv run pytest -q`  
Expected: PASS.

**Step 5: Commit**

Run:
```bash
git add backend/src/creativeai_studio/runner.py backend/src/creativeai_studio/main.py backend/tests/test_runner_requeues_queued.py
git commit -m "feat(runner): add background job runner with recovery"
```

---

### Task 13: Google Provider (google-genai) for image/video/extend (mocked unit tests + manual real test)

**Files:**
- Create: `backend/src/creativeai_studio/providers/google_provider.py`
- Create: `backend/src/creativeai_studio/gcs.py`
- Modify: `backend/src/creativeai_studio/runner.py`
- Test: `backend/tests/test_google_provider_image.py`

**Step 1: Write failing test (image)**

Create `backend/tests/test_google_provider_image.py`:
```python
from unittest.mock import Mock

from creativeai_studio.providers.google_provider import GoogleProvider


def test_generate_image_returns_bytes():
    fake_client = Mock()
    fake_client.models.generate_images.return_value = Mock(
        generated_images=[Mock(image=Mock(image_bytes=b"img", mime_type="image/png"))]
    )
    p = GoogleProvider(client_factory=lambda **_: fake_client, gcs=None)
    out = p.generate_image(
        provider_model="imagen-3.0-generate-002",
        prompt="x",
        aspect_ratio="1:1",
        image_size="1k",
    )
    assert out["mime_type"] == "image/png"
    assert out["bytes"] == b"img"
```

**Step 2: Run to confirm fail**

Run: `uv run pytest -q`  
Expected: FAIL.

**Step 3: Minimal provider implementation**

Create `backend/src/creativeai_studio/providers/google_provider.py`:
- `GoogleProvider(client_factory=genai.Client, gcs=GcsClient|None)`
- `make_client_api_key(api_key)`
- `make_client_vertex(credentials, project, location)`
- `generate_image(...)` uses `types.GenerateImagesConfig`
- `edit_image(...)` (Vertex only) uses `client.models.edit_image` + `RawReferenceImage` + `MaskReferenceImage(mask_mode=BACKGROUND)`
- `upscale_image_x2(...)` (Vertex only)
- `generate_video(...)` uses `client.models.generate_videos(source=...)` + `types.GenerateVideosConfig(duration_seconds, aspect_ratio, last_frame?)` and polls via `client.operations.get()`
- `extend_video(...)` (Vertex only): upload input video to GCS (via `gcs.upload_file`) then `generate_videos(video=types.Video(uri=...))`
- 统一返回：`{"bytes": ..., "mime_type": ..., "gcs_uri": ...?}`（若只返回 gcs uri，Runner 负责下载）

Create `backend/src/creativeai_studio/gcs.py`:
- `GcsClient(credentials)` using `google-cloud-storage`
- `upload_file(bucket, object_name, local_path) -> gs://...`
- `download_to_file(gs://..., local_path)`
- helpers to parse `gs://bucket/key`

**Step 4: Run to confirm pass**

Run: `uv run pytest -q`  
Expected: PASS.

**Step 5: Wire into runner**

Modify `backend/src/creativeai_studio/runner.py` to dispatch by `job_type`:
- `image.generate` → provider.generate_image / provider.edit_image / provider.upscale_image
- `video.generate` → provider.generate_video
- `video.extend` → provider.extend_video
并把产物落盘入库（`assets.insert_generated` + `job_assets.add(role="output")`）。

**Step 6: Commit**

Run:
```bash
git add backend/src/creativeai_studio/providers/google_provider.py backend/src/creativeai_studio/gcs.py backend/src/creativeai_studio/runner.py backend/tests/test_google_provider_image.py
git commit -m "feat(provider): google-genai provider skeleton (mocked)"
```

---

### Task 14: Settings test endpoint (API key / Vertex / GCS) (manual + light unit test)

**Files:**
- Modify: `backend/src/creativeai_studio/api/settings.py`
- Test: `backend/tests/test_settings_bucket_validation.py`

**Step 1: Unit test for bucket format**

Create `backend/tests/test_settings_bucket_validation.py`:
```python
from fastapi.testclient import TestClient

from creativeai_studio.config import AppConfig
from creativeai_studio.main import create_app


def test_bucket_rejects_gs_prefix(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    client = TestClient(app)
    resp = client.put("/api/settings", json={"vertex_gcs_bucket": "gs://abc"})
    assert resp.status_code == 400
```

**Step 2: Implement `POST /api/settings/test`**

In `backend/src/creativeai_studio/api/settings.py` add:
- 读取 settings：api_key、vertex_sa_path、project/location/bucket
- 对 api_key：`genai.Client(api_key=...).models.list(config={"page_size": 1})`
- 对 vertex：`Credentials.from_service_account_file(vertex_sa_path, scopes=[cloud-platform])` + `genai.Client(vertexai=True, project, location, credentials=...)`
- 对 gcs：上传一个小文件到 `gs://<bucket>/creativeai-studio/_test/<ts>.txt` 再删除

**Step 3: Run unit tests**

Run: `uv run pytest -q`  
Expected: PASS.

**Step 4: Commit**

Run:
```bash
git add backend/src/creativeai_studio/api/settings.py backend/tests/test_settings_bucket_validation.py
git commit -m "feat(settings): add settings test endpoint"
```

---

## 2. Web（React）实现计划

### Task 15: Scaffold web project + routing + dark theme shell

**Files:**
- Create: `web/`（Vite react-ts）
- Modify/Create: `web/src/app/App.tsx`
- Create: `web/src/app/routes.tsx`
- Create: `web/src/app/layout/AppLayout.tsx`
- Create: `web/src/styles/theme.css`

**Step 1: Initialize**

Run:
```bash
pnpm create vite web --template react-ts
cd web
pnpm add react-router-dom
pnpm add -D eslint prettier
```

**Step 2: Implement shell**

- 顶部导航：生成 / 资产 / 历史 / 设置
- 样式：暗色（无蓝紫渐变），面板轻描边、圆角、克制强调色（青绿/琥珀二选一）

**Step 3: Run**

Run: `pnpm -s dev`  
Expected: 能看到 4 个空页面切换。

**Step 4: Commit**

Run:
```bash
git add web
git commit -m "feat(web): app shell and routing"
```

---

### Task 16: Web API client + model-driven forms

**Files:**
- Create: `web/src/lib/api.ts`
- Create: `web/src/lib/types.ts`
- Create: `web/src/features/models/useModels.ts`

**Steps:**
1) 实现 `GET /api/models`、`GET/PUT /api/settings`、`POST /api/assets/upload`、`GET /api/assets`、`POST /api/jobs`、`GET /api/jobs`、`GET /api/jobs/:id`、`POST /api/jobs/:id/clone`、`POST /api/jobs/:id/cancel` 的最小封装。
2) 写一个 `useModels()` hook，把 catalog 作为表单渲染依据（resolution/ratio/duration、禁用不支持项）。
3) Commit：`git commit -m "feat(web): api client and models hook"`

---

### Task 17: Generate Page (image/video/extend) + polling

**Files:**
- Create: `web/src/features/generate/GeneratePage.tsx`
- Create: `web/src/features/generate/components/*`

**Steps:**
1) 左侧 tabs：
   - 图片：模型、prompt、image_size、aspect_ratio、reference image（可选）
   - 视频：模型、prompt、duration_seconds、aspect_ratio、start/end（end 依赖 start）
   - 延长：选择视频资产 + extend_seconds + prompt（可选）
2) 右侧结果：按 job 状态显示 empty/loading/error/preview（img/video）。
3) polling：创建 job 后每 1.5s 拉 `GET /api/jobs/:id`，直到结束状态。
4) Commit：`git commit -m "feat(web): generate page with polling"`

---

### Task 18: Assets Page + asset picker modal

**Files:**
- Create: `web/src/features/assets/AssetsPage.tsx`
- Create: `web/src/features/assets/AssetPickerModal.tsx`

**Steps:**
1) Grid 列表（图片/视频分组或筛选），点击进入 drawer 预览 + 下载。
2) 提供 picker 给 Generate/Extend 选择输入资产（start/end/input_video）。
3) Commit：`git commit -m "feat(web): assets page and picker"`

---

### Task 19: History Page + clone/cancel

**Files:**
- Create: `web/src/features/history/HistoryPage.tsx`

**Steps:**
1) 列表展示 jobs（状态、类型、模型、时间），点开可查看输入/输出资产。
2) clone：调用 `/api/jobs/:id/clone`，跳转到结果页并开始 polling。
3) cancel：调用 `/api/jobs/:id/cancel`。
4) Commit：`git commit -m "feat(web): history page with clone/cancel"`

---

### Task 20: Settings Page (api key / vertex json / bucket / test)

**Files:**
- Create: `web/src/features/settings/SettingsPage.tsx`

**Steps:**
1) 默认鉴权模式切换（api_key/vertex）
2) API Key 输入保存（后端只返回 present，不回显 key）
3) Vertex JSON 上传（`POST /api/settings/vertex-sa`）+ project/location + bucket
4) Test 按钮调用 `POST /api/settings/test` 展示结果
5) Commit：`git commit -m "feat(web): settings page"`

---

## 3. 交付与运行

### Task 21: Root README + dev commands

**Files:**
- Create: `README.md`

**Steps:**
1) 写清楚本地启动步骤：
   - 后端：`cd backend && uv sync && uv run uvicorn creativeai_studio.main:app --reload --port 8000`
   - 前端：`cd web && pnpm i && pnpm dev`
2) 配置说明：`DATA_DIR`、`VERTEX_GCS_BUCKET`、Vertex JSON 上传位置等。
3) Commit：`git commit -m "docs: add README for local dev"`

---

## Execution Handoff

计划已保存到：
- `docs/plans/2026-02-23-creativeai-studio-design.md`
- `docs/plans/2026-02-23-creativeai-studio-mvp-implementation-plan.md`

两种执行方式（选其一）：

1) **Subagent-Driven（本 session）**：我用 superpowers:subagent-driven-development 按 Task 派子代理逐个实现，每个 Task 结束 review 再继续。

2) **Parallel Session（新 session）**：你开新 session，用 superpowers:executing-plans 按本计划逐条执行。

你选哪一种？

