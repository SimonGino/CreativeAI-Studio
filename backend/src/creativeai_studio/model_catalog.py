from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

def _default_catalog_path() -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / "catalog" / "models.json"


def _catalog_path() -> Path:
    override = os.getenv("MODEL_CATALOG_PATH")
    if override:
        return Path(override)
    return _default_catalog_path()


@lru_cache(maxsize=1)
def _load_catalog() -> list[dict[str, Any]]:
    path = _catalog_path()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("Model catalog must be a JSON list")
    out: list[dict[str, Any]] = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"Model catalog entry #{idx} must be an object")
        if not item.get("model_id"):
            raise ValueError(f"Model catalog entry #{idx} missing model_id")
        out.append(item)
    return out


def list_models() -> list[dict[str, Any]]:
    return _load_catalog()


def get_model(model_id: str) -> dict[str, Any] | None:
    for m in _load_catalog():
        if m["model_id"] == model_id:
            return m
    return None


def reload_model_catalog() -> None:
    _load_catalog.cache_clear()
