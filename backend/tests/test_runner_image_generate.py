from io import BytesIO

from PIL import Image

from creativeai_studio.config import AppConfig
from creativeai_studio.main import create_app
from creativeai_studio.runner import JobRunner


class _DummyProvider:
    def make_client_api_key(self, api_key: str):  # noqa: ARG002
        return object()

    def __init__(self):
        self.last_provider_model: str | None = None

    def generate_image(self, *, provider_model: str, **__):
        self.last_provider_model = provider_model
        buf = BytesIO()
        Image.new("RGB", (8, 8), color=(255, 0, 0)).save(buf, format="PNG")
        return {"bytes": buf.getvalue(), "mime_type": "image/png"}


def test_runner_image_generate_stores_asset(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    ctx = app.state.ctx
    ctx.settings.set_str("google_api_key", "x")

    ctx.jobs.create(
        job_id="j1",
        job_type="image.generate",
        model_id="nano-banana-pro",
        auth_mode="api_key",
        params={"prompt": "x", "aspect_ratio": "1:1", "image_size": "1k"},
    )

    provider = _DummyProvider()
    runner = JobRunner(ctx, provider=provider, concurrency=1)
    runner._run_one("j1")

    job = ctx.jobs.get("j1")
    assert job is not None
    assert job["status"] == "succeeded"
    assert provider.last_provider_model == "gemini-3-pro-image-preview"
    assert job["result"]["outputs"]
    assert job["result"]["outputs"][0]["media_type"] == "image"
    assert job["result"]["output_asset_id"] == job["result"]["outputs"][0]["asset_id"]

    asset = ctx.assets.get(job["result"]["outputs"][0]["asset_id"])
    assert asset is not None
    assert asset["media_type"] == "image"
