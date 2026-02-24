from __future__ import annotations

import mimetypes
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StoredFile:
    rel_path: str
    abs_path: Path
    mime_type: str
    size_bytes: int


class AssetStore:
    def __init__(self, data_dir: Path):
        self._data_dir = data_dir

    def save_upload(self, asset_id: str, filename: str, content: bytes) -> StoredFile:
        ext = Path(filename).suffix.lower()
        rel = Path("assets/uploads") / f"{asset_id}{ext}"
        return self._write(rel, content)

    def save_generated(self, asset_id: str, ext: str, content: bytes) -> StoredFile:
        ext = ext if ext.startswith(".") else f".{ext}"
        rel = Path("assets/generated") / f"{asset_id}{ext}"
        return self._write(rel, content)

    def save_generated_from_file(self, asset_id: str, ext: str, src_path: Path) -> StoredFile:
        ext = ext if ext.startswith(".") else f".{ext}"
        rel = Path("assets/generated") / f"{asset_id}{ext}"
        abs_path = (self._data_dir / rel).resolve()
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src_path, abs_path)
        size_bytes = abs_path.stat().st_size
        mime_type = mimetypes.guess_type(str(abs_path))[0] or "application/octet-stream"
        return StoredFile(rel_path=str(rel), abs_path=abs_path, mime_type=mime_type, size_bytes=size_bytes)

    def resolve(self, rel_path: str) -> Path:
        p = (self._data_dir / rel_path).resolve()
        if self._data_dir not in p.parents and p != self._data_dir:
            raise ValueError("Invalid asset path")
        return p

    def _write(self, rel: Path, content: bytes) -> StoredFile:
        abs_path = (self._data_dir / rel).resolve()
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_bytes(content)
        size_bytes = abs_path.stat().st_size
        mime_type = mimetypes.guess_type(str(abs_path))[0] or "application/octet-stream"
        return StoredFile(rel_path=str(rel), abs_path=abs_path, mime_type=mime_type, size_bytes=size_bytes)
