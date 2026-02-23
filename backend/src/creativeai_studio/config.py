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
