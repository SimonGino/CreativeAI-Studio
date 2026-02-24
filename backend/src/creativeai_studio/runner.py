from __future__ import annotations

import mimetypes
import queue
import threading
import uuid
from pathlib import Path
from typing import Any

from creativeai_studio.api.deps import AppContext
from creativeai_studio.media_meta import read_image_size
from creativeai_studio.model_catalog import get_model


def _load_vertex_credentials(sa_path: str):
    from google.oauth2.service_account import Credentials

    return Credentials.from_service_account_file(
        sa_path,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )


class JobRunner:
    def __init__(
        self,
        ctx: AppContext,
        provider: Any = None,
        *,
        gcs: Any | None = None,
        vertex_credentials_factory: Any | None = None,
        concurrency: int = 1,
    ):
        self._ctx = ctx
        self._provider = provider
        self._gcs = gcs
        self._vertex_credentials_factory = vertex_credentials_factory or _load_vertex_credentials
        self._q: queue.Queue[str] = queue.Queue()
        self._started = False
        self._lock = threading.Lock()
        self._concurrency = max(1, int(concurrency))

    def qsize(self) -> int:
        return self._q.qsize()

    def enqueue(self, job_id: str) -> None:
        self._q.put(job_id)

    def recover_on_startup(self) -> None:
        for j in self._ctx.jobs.list(status="running", limit=1000, offset=0):
            self._ctx.jobs.set_failed(j["id"], "server restarted")

        for j in self._ctx.jobs.list(status="queued", limit=1000, offset=0):
            self.enqueue(j["id"])

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            self._started = True

        for i in range(self._concurrency):
            t = threading.Thread(target=self._worker_loop, name=f"job-runner-{i}", daemon=True)
            t.start()

    def _worker_loop(self) -> None:
        while True:
            job_id = self._q.get()
            try:
                self._run_one(job_id)
            finally:
                self._q.task_done()

    def _run_one(self, job_id: str) -> None:
        job = self._ctx.jobs.get(job_id)
        if not job:
            return

        if job.get("cancel_requested"):
            self._ctx.jobs.set_status(job_id, "canceled")
            return

        if job.get("status") != "queued":
            return

        self._ctx.jobs.set_status(job_id, "running")
        try:
            if self._provider is None:
                raise RuntimeError("Provider not configured")
            result = self._dispatch(job)
            self._ctx.jobs.set_succeeded(job_id, result_dict=result or {})
        except Exception as e:  # noqa: BLE001
            self._ctx.jobs.set_failed(job_id, "job failed", detail=str(e))

    def _dispatch(self, job: dict[str, Any]) -> dict[str, Any]:
        job_type = job.get("job_type")
        if job_type == "image.generate":
            return self._run_image_generate(job)
        if job_type == "video.generate":
            return self._run_video_generate(job)
        if job_type == "video.extend":
            return self._run_video_extend(job)
        raise NotImplementedError(f"Unsupported job_type: {job_type}")

    def _run_image_generate(self, job: dict[str, Any]) -> dict[str, Any]:
        model = get_model(str(job.get("model_id") or ""))
        if model is None:
            raise RuntimeError("Unknown model_id")
        provider_models = model.get("provider_models") or {}
        provider_model = (
            provider_models.get("image_generate") or model.get("provider_model") or model.get("model_id")
        )
        provider_model_edit = (
            provider_models.get("image_edit") or model.get("provider_model_edit") or provider_model
        )

        params = job.get("params") or {}

        client = self._make_client(job)

        aspect_ratio = str(params.get("aspect_ratio") or "1:1")
        prompt = str(params.get("prompt") or "")

        if params.get("reference_image_asset_id"):
            ref_id = str(params["reference_image_asset_id"])
            ref = self._ctx.assets.get(ref_id)
            if not ref:
                raise RuntimeError("Reference image asset not found")
            ref_path = self._ctx.asset_store.resolve(ref["file_path"])
            ref_bytes = ref_path.read_bytes()
            ref_mime = str(ref.get("mime_type") or "image/png")
            if job.get("auth_mode") == "vertex":
                out = self._provider.edit_image(
                    provider_model=str(provider_model_edit),
                    prompt=prompt,
                    reference_image_bytes=ref_bytes,
                    reference_image_mime_type=ref_mime,
                    aspect_ratio=aspect_ratio,
                    client=client,
                )
            else:
                out = self._provider.generate_image(
                    provider_model=str(provider_model),
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                    image_size=str(params.get("image_size") or "1k"),
                    reference_image_bytes=ref_bytes,
                    reference_image_mime_type=ref_mime,
                    client=client,
                )
        else:
            out = self._provider.generate_image(
                provider_model=str(provider_model),
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                image_size=str(params.get("image_size") or "1k"),
                client=client,
            )

        mime_type = str(out.get("mime_type") or "application/octet-stream")
        ext = mimetypes.guess_extension(mime_type) or ".bin"
        asset_id = uuid.uuid4().hex
        stored = self._ctx.asset_store.save_generated(asset_id=asset_id, ext=ext, content=out["bytes"])
        width, height = read_image_size(stored.abs_path)

        self._ctx.assets.insert_generated(
            asset_id=asset_id,
            media_type="image",
            file_path=stored.rel_path,
            mime_type=mime_type,
            size_bytes=stored.size_bytes,
            source_job_id=str(job["id"]),
            width=width,
            height=height,
        )
        self._ctx.job_assets.add(job_id=str(job["id"]), asset_id=asset_id, role="output")

        return {"output_asset_id": asset_id}

    def _run_video_generate(self, job: dict[str, Any]) -> dict[str, Any]:
        model = get_model(str(job.get("model_id") or ""))
        if model is None:
            raise RuntimeError("Unknown model_id")
        provider_models = model.get("provider_models") or {}
        provider_model = (
            provider_models.get("video_generate") or model.get("provider_model") or model.get("model_id")
        )

        params = job.get("params") or {}
        client = self._make_client(job)

        start_image = self._load_image_bytes(params.get("start_image_asset_id"))
        end_image = self._load_image_bytes(params.get("end_image_asset_id"))

        out = self._provider.generate_video(
            provider_model=str(provider_model),
            prompt=str(params.get("prompt") or ""),
            duration_seconds=int(params.get("duration_seconds") or 5),
            aspect_ratio=str(params.get("aspect_ratio") or "16:9"),
            start_image=start_image,
            end_image=end_image,
            client=client,
        )

        mime_type = str(out.get("mime_type") or "video/mp4")
        ext = mimetypes.guess_extension(mime_type) or ".mp4"
        asset_id = uuid.uuid4().hex

        if "bytes" in out:
            stored = self._ctx.asset_store.save_generated(asset_id=asset_id, ext=ext, content=out["bytes"])
        else:
            stored = self._download_video_output(asset_id=asset_id, ext=ext, out=out)

        self._ctx.assets.insert_generated(
            asset_id=asset_id,
            media_type="video",
            file_path=stored.rel_path,
            mime_type=mime_type,
            size_bytes=stored.size_bytes,
            source_job_id=str(job["id"]),
        )
        self._ctx.job_assets.add(job_id=str(job["id"]), asset_id=asset_id, role="output")
        return {"output_asset_id": asset_id}

    def _run_video_extend(self, job: dict[str, Any]) -> dict[str, Any]:
        if job.get("auth_mode") != "vertex":
            raise RuntimeError("video.extend requires vertex auth")

        model = get_model(str(job.get("model_id") or ""))
        if model is None:
            raise RuntimeError("Unknown model_id")
        provider_models = model.get("provider_models") or {}
        provider_model = (
            provider_models.get("video_extend") or model.get("provider_model") or model.get("model_id")
        )

        params = job.get("params") or {}
        input_asset_id = str(params.get("input_video_asset_id") or "")
        if not input_asset_id:
            raise RuntimeError("input_video_asset_id is required")

        bucket = self._ctx.settings.get_str("vertex_gcs_bucket")
        if not bucket:
            raise RuntimeError("vertex_gcs_bucket not configured")

        parent = self._ctx.assets.get(input_asset_id)
        if not parent:
            raise RuntimeError("Input video asset not found")
        input_path = self._ctx.asset_store.resolve(parent["file_path"])

        credentials, project, location = self._get_vertex_creds_and_config()
        client = self._provider.make_client_vertex(credentials=credentials, project=project, location=location)

        gcs = self._gcs
        if gcs is None:
            from creativeai_studio.gcs import GcsClient

            gcs = GcsClient(project=project, credentials=credentials)

        input_ext = Path(input_path).suffix or ".mp4"
        input_uri = gcs.upload_file(
            bucket=bucket,
            object_name=f"creativeai-studio/{job['id']}/input{input_ext}",
            local_path=input_path,
        )

        out = self._provider.extend_video(
            provider_model=str(provider_model),
            input_video_uri=input_uri,
            extend_seconds=int(params.get("extend_seconds") or 5),
            prompt=str(params.get("prompt") or "") or None,
            aspect_ratio=str(params.get("aspect_ratio") or "") or None,
            output_gcs_uri=f"gs://{bucket}/creativeai-studio/{job['id']}/",
            client=client,
        )

        mime_type = str(out.get("mime_type") or "video/mp4")
        ext = mimetypes.guess_extension(mime_type) or ".mp4"
        asset_id = uuid.uuid4().hex

        if "bytes" in out:
            stored = self._ctx.asset_store.save_generated(asset_id=asset_id, ext=ext, content=out["bytes"])
        else:
            stored = self._download_video_output(asset_id=asset_id, ext=ext, out=out, gcs=gcs)

        self._ctx.assets.insert_generated(
            asset_id=asset_id,
            media_type="video",
            file_path=stored.rel_path,
            mime_type=mime_type,
            size_bytes=stored.size_bytes,
            source_job_id=str(job["id"]),
            parent_asset_id=input_asset_id,
        )
        self._ctx.job_assets.add(job_id=str(job["id"]), asset_id=asset_id, role="output")
        return {"output_asset_id": asset_id}

    def _load_image_bytes(self, asset_id: Any) -> dict[str, Any] | None:
        if not asset_id:
            return None
        a = self._ctx.assets.get(str(asset_id))
        if not a:
            raise RuntimeError("Image asset not found")
        p = self._ctx.asset_store.resolve(a["file_path"])
        return {"bytes": p.read_bytes(), "mime_type": a.get("mime_type")}

    def _make_client(self, job: dict[str, Any]):
        auth_mode = job.get("auth_mode")
        if auth_mode == "api_key":
            api_key = self._ctx.settings.get_str("google_api_key")
            if not api_key:
                raise RuntimeError("google_api_key not configured")
            return self._provider.make_client_api_key(api_key)
        if auth_mode == "vertex":
            credentials, project, location = self._get_vertex_creds_and_config()
            return self._provider.make_client_vertex(credentials=credentials, project=project, location=location)
        raise RuntimeError("Unknown auth mode")

    def _get_vertex_creds_and_config(self):
        sa_path = self._ctx.settings.get_str("vertex_sa_path")
        project = self._ctx.settings.get_str("vertex_project_id")
        location = self._ctx.settings.get_str("vertex_location")
        if not sa_path or not project or not location:
            raise RuntimeError("Vertex settings not configured")
        credentials = self._vertex_credentials_factory(sa_path)
        return credentials, project, location

    def _download_video_output(self, *, asset_id: str, ext: str, out: dict[str, Any], gcs: Any | None = None):
        uri = out.get("gcs_uri")
        if not uri:
            raise RuntimeError("No video uri")

        tmp_path = self._ctx.cfg.data_dir / "tmp" / f"{asset_id}{ext}"
        if uri.startswith("gs://"):
            if gcs is None:
                raise RuntimeError("GCS client not configured")
            gcs.download_to_file(uri, tmp_path)
        elif uri.startswith("http://") or uri.startswith("https://"):
            import urllib.request

            tmp_path.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(uri, tmp_path)  # noqa: S310
        else:
            raise RuntimeError("Unsupported video uri")

        return self._ctx.asset_store.save_generated_from_file(asset_id=asset_id, ext=ext, src_path=tmp_path)
