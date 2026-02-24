from __future__ import annotations

import base64
import mimetypes
import queue
import threading
import urllib.request
import uuid
from typing import Any

from creativeai_studio.api.deps import AppContext
from creativeai_studio.media_meta import read_image_size
from creativeai_studio.model_catalog import get_model


class JobRunner:
    def __init__(
        self,
        ctx: AppContext,
        provider: Any = None,
        *,
        providers: dict[str, Any] | None = None,
        concurrency: int = 1,
    ):
        self._ctx = ctx
        self._providers: dict[str, Any] = dict(providers or {})
        if provider is not None and "google" not in self._providers:
            self._providers["google"] = provider
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
            result = self._dispatch(job)
            self._ctx.jobs.set_succeeded(job_id, result_dict=result or {})
        except Exception as e:  # noqa: BLE001
            error_message, error_detail = self._format_job_error(job=job, error=e)
            self._ctx.jobs.set_failed(job_id, error_message, detail=error_detail)

    def _dispatch(self, job: dict[str, Any]) -> dict[str, Any]:
        job_type = job.get("job_type")
        if job_type == "image.generate":
            return self._run_image_generate(job)
        if job_type == "video.generate":
            return self._run_video_generate(job)
        raise NotImplementedError(f"Unsupported job_type: {job_type}")

    def _run_image_generate(self, job: dict[str, Any]) -> dict[str, Any]:
        model = get_model(str(job.get("model_id") or ""))
        if model is None:
            raise RuntimeError("Unknown model_id")
        provider = self._get_provider_for_model(model)
        if provider is None:
            raise RuntimeError("Provider not configured")
        provider_models = model.get("provider_models") or {}
        provider_model = (
            provider_models.get("image_generate") or model.get("provider_model") or model.get("model_id")
        )

        params = job.get("params") or {}

        client = self._make_client(job=job, model=model, provider=provider)

        aspect_ratio = str(params.get("aspect_ratio") or "1:1")
        prompt = str(params.get("prompt") or "")
        watermark = params.get("watermark")
        sequential_image_generation = params.get("sequential_image_generation")
        sequential_image_generation_options = params.get("sequential_image_generation_options")
        ref_ids = self._get_reference_image_asset_ids(params)
        refs = [self._load_image_bytes(ref_id) for ref_id in ref_ids]
        refs = [r for r in refs if r is not None]

        if refs:
            first_ref = refs[0]
            out = provider.generate_image(
                provider_model=str(provider_model),
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                image_size=str(params.get("image_size") or "1k"),
                reference_image_bytes=first_ref["bytes"],
                reference_image_mime_type=str(first_ref.get("mime_type") or "image/png"),
                reference_images=refs,
                sequential_image_generation=(
                    str(sequential_image_generation)
                    if sequential_image_generation is not None
                    else None
                ),
                sequential_image_generation_options=(
                    dict(sequential_image_generation_options)
                    if isinstance(sequential_image_generation_options, dict)
                    else None
                ),
                watermark=bool(watermark) if watermark is not None else None,
                client=client,
            )
        else:
            out = provider.generate_image(
                provider_model=str(provider_model),
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                image_size=str(params.get("image_size") or "1k"),
                sequential_image_generation=(
                    str(sequential_image_generation) if sequential_image_generation is not None else None
                ),
                sequential_image_generation_options=(
                    dict(sequential_image_generation_options)
                    if isinstance(sequential_image_generation_options, dict)
                    else None
                ),
                watermark=bool(watermark) if watermark is not None else None,
                client=client,
            )

        outputs = self._store_image_outputs(job_id=str(job["id"]), out=out)
        return self._result_with_outputs(outputs)

    def _run_video_generate(self, job: dict[str, Any]) -> dict[str, Any]:
        model = get_model(str(job.get("model_id") or ""))
        if model is None:
            raise RuntimeError("Unknown model_id")
        provider = self._get_provider_for_model(model)
        if provider is None:
            raise RuntimeError("Provider not configured")
        provider_models = model.get("provider_models") or {}
        provider_model = (
            provider_models.get("video_generate") or model.get("provider_model") or model.get("model_id")
        )

        params = job.get("params") or {}
        client = self._make_client(job=job, model=model, provider=provider)

        start_image = self._load_image_bytes(params.get("start_image_asset_id"))
        end_image = self._load_image_bytes(params.get("end_image_asset_id"))

        out = provider.generate_video(
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
        return self._result_with_outputs(
            [{"asset_id": asset_id, "media_type": "video", "role": "output", "index": 0}]
        )

    def _load_image_bytes(self, asset_id: Any) -> dict[str, Any] | None:
        if not asset_id:
            return None
        a = self._ctx.assets.get(str(asset_id))
        if not a:
            raise RuntimeError("Image asset not found")
        p = self._ctx.asset_store.resolve(a["file_path"])
        return {"bytes": p.read_bytes(), "mime_type": a.get("mime_type")}

    def _make_client(self, *, job: dict[str, Any], model: dict[str, Any], provider: Any):
        provider_id = str(model.get("provider_id") or "google")
        auth_mode = job.get("auth_mode")
        if auth_mode == "api_key":
            setting_key = self._api_key_setting_for_provider(provider_id)
            api_key = self._ctx.settings.get_str(setting_key)
            if not api_key:
                raise RuntimeError(f"{setting_key} not configured")
            if not hasattr(provider, "make_client_api_key"):
                raise RuntimeError("Provider does not support api_key auth")
            return provider.make_client_api_key(api_key)
        raise RuntimeError("Unknown auth mode")

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

    def _get_provider_for_model(self, model: dict[str, Any]) -> Any | None:
        provider_id = str(model.get("provider_id") or "google")
        return self._providers.get(provider_id)

    @staticmethod
    def _api_key_setting_for_provider(provider_id: str) -> str:
        if provider_id == "google":
            return "google_api_key"
        if provider_id == "volcengine_ark":
            return "ark_api_key"
        raise RuntimeError(f"Unsupported provider_id for api_key auth: {provider_id}")

    @staticmethod
    def _get_reference_image_asset_ids(params: dict[str, Any]) -> list[str]:
        ids: list[str] = []
        multi = params.get("reference_image_asset_ids")
        if isinstance(multi, list):
            for item in multi:
                value = str(item or "").strip()
                if value:
                    ids.append(value)
        single = str(params.get("reference_image_asset_id") or "").strip()
        if single and single not in ids:
            ids.insert(0, single)
        return ids

    def _store_image_outputs(self, *, job_id: str, out: dict[str, Any]) -> list[dict[str, Any]]:
        raw_items = out.get("items")
        items: list[dict[str, Any]]
        if isinstance(raw_items, list):
            items = [dict(item) if isinstance(item, dict) else {"value": item} for item in raw_items]
        else:
            items = [out]

        outputs: list[dict[str, Any]] = []
        for idx, item in enumerate(items):
            asset_id = self._store_image_output_asset(job_id=job_id, item=item)
            outputs.append({"asset_id": asset_id, "media_type": "image", "role": "output", "index": idx})
        return outputs

    def _store_image_output_asset(self, *, job_id: str, item: dict[str, Any]) -> str:
        content, mime_type = self._read_image_output_bytes(item)
        ext = mimetypes.guess_extension(mime_type) or ".bin"
        asset_id = uuid.uuid4().hex
        stored = self._ctx.asset_store.save_generated(asset_id=asset_id, ext=ext, content=content)
        width, height = read_image_size(stored.abs_path)

        self._ctx.assets.insert_generated(
            asset_id=asset_id,
            media_type="image",
            file_path=stored.rel_path,
            mime_type=mime_type,
            size_bytes=stored.size_bytes,
            source_job_id=job_id,
            width=width,
            height=height,
        )
        self._ctx.job_assets.add(job_id=job_id, asset_id=asset_id, role="output")
        return asset_id

    @staticmethod
    def _read_image_output_bytes(item: dict[str, Any]) -> tuple[bytes, str]:
        raw = item.get("bytes")
        if isinstance(raw, (bytes, bytearray, memoryview)):
            return bytes(raw), str(item.get("mime_type") or "image/png")

        b64_json = item.get("b64_json")
        if isinstance(b64_json, str) and b64_json:
            return base64.b64decode(b64_json), str(item.get("mime_type") or "image/png")

        url = item.get("url")
        if isinstance(url, str) and url:
            with urllib.request.urlopen(url) as resp:  # noqa: S310
                content = resp.read()
                mime_type = resp.headers.get_content_type() or "image/png"
            return content, mime_type

        raise RuntimeError("Unsupported image output item")

    @staticmethod
    def _result_with_outputs(outputs: list[dict[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {"outputs": outputs}
        if outputs:
            out["output_asset_id"] = outputs[0]["asset_id"]
        return out

    @staticmethod
    def _format_job_error(*, job: dict[str, Any], error: Exception) -> tuple[str, str]:
        detail = str(error)
        job_type = str(job.get("job_type") or "")
        model_id = str(job.get("model_id") or "")

        if (
            "503 UNAVAILABLE" in detail
            or "currently experiencing high demand" in detail
            or "'status': 'UNAVAILABLE'" in detail
        ):
            return (
                "模型服务繁忙（请求高峰）。这通常是临时问题，请稍后重试。",
                detail,
            )

        if (
            job_type == "image.generate"
            and model_id in {"nano-banana", "nano-banana-pro"}
            and "No image output" in detail
        ):
            return (
                "图片未生成成功：模型没有返回图片结果。请尝试改写提示词（优先使用原创描述，避免直接使用知名 IP 角色/品牌名），或降低敏感/冲突表述后重试。",
                detail,
            )

        return ("job failed", detail)
