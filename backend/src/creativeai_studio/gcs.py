from __future__ import annotations

from pathlib import Path
from typing import Any

from google.cloud import storage


def parse_gs_uri(gs_uri: str) -> tuple[str, str]:
    if not gs_uri.startswith("gs://"):
        raise ValueError("Invalid GCS uri")
    rest = gs_uri[len("gs://") :]
    if not rest:
        raise ValueError("Invalid GCS uri")
    bucket, _, key = rest.partition("/")
    return bucket, key


class GcsClient:
    def __init__(self, *, project: str | None, credentials: Any):
        self._client = storage.Client(project=project, credentials=credentials)

    def upload_file(self, bucket: str, object_name: str, local_path: Path) -> str:
        blob = self._client.bucket(bucket).blob(object_name)
        blob.upload_from_filename(str(local_path))
        return f"gs://{bucket}/{object_name}"

    def download_to_file(self, gs_uri: str, local_path: Path) -> None:
        bucket, key = parse_gs_uri(gs_uri)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        blob = self._client.bucket(bucket).blob(key)
        blob.download_to_filename(str(local_path))

