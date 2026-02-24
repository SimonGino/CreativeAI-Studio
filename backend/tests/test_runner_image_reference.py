from io import BytesIO

from PIL import Image

from creativeai_studio.config import AppConfig
from creativeai_studio.main import create_app
from creativeai_studio.runner import JobRunner


class _DummyProvider:
    def make_client_vertex(self, **_):
        return object()

    def __init__(self):
        self.last_provider_model: str | None = None

    def edit_image(self, *, provider_model: str, **__):
        self.last_provider_model = provider_model
        buf = BytesIO()
        Image.new("RGB", (8, 8), color=(0, 255, 0)).save(buf, format="PNG")
        return {"bytes": buf.getvalue(), "mime_type": "image/png"}


def test_runner_image_generate_with_reference_uses_vertex(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    ctx = app.state.ctx

    img = BytesIO()
    Image.new("RGB", (4, 4), color=(0, 0, 0)).save(img, format="PNG")
    stored = ctx.asset_store.save_upload(asset_id="a1", filename="ref.png", content=img.getvalue())
    ctx.assets.insert_upload(
        asset_id="a1",
        media_type="image",
        file_path=stored.rel_path,
        mime_type="image/png",
        size_bytes=stored.size_bytes,
        width=4,
        height=4,
    )

    ctx.settings.set_str("vertex_sa_path", str(ctx.cfg.data_dir / "credentials" / "vertex-sa.json"))
    ctx.settings.set_str("vertex_project_id", "p")
    ctx.settings.set_str("vertex_location", "us-central1")

    ctx.jobs.create(
        job_id="j1",
        job_type="image.generate",
        model_id="nano-banana-pro",
        auth_mode="vertex",
        params={
            "prompt": "x",
            "aspect_ratio": "1:1",
            "reference_image_asset_id": "a1",
        },
    )

    runner = JobRunner(
        ctx,
        provider=(provider := _DummyProvider()),
        vertex_credentials_factory=lambda _: object(),
        concurrency=1,
    )
    runner._run_one("j1")

    job = ctx.jobs.get("j1")
    assert job is not None
    assert job["status"] == "succeeded"
    assert provider.last_provider_model == "imagen-3.0-capability-001"


class _DummyProviderApiKey:
    def make_client_api_key(self, api_key: str):  # noqa: ARG002
        return object()

    def __init__(self):
        self.last_provider_model: str | None = None
        self.last_had_reference: bool = False

    def generate_image(self, *, provider_model: str, reference_image_bytes=None, **__):
        self.last_provider_model = provider_model
        self.last_had_reference = bool(reference_image_bytes)
        buf = BytesIO()
        Image.new("RGB", (8, 8), color=(0, 0, 255)).save(buf, format="PNG")
        return {"bytes": buf.getvalue(), "mime_type": "image/png"}


def test_runner_image_generate_with_reference_allows_api_key(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    ctx = app.state.ctx

    img = BytesIO()
    Image.new("RGB", (4, 4), color=(0, 0, 0)).save(img, format="PNG")
    stored = ctx.asset_store.save_upload(asset_id="a1", filename="ref.png", content=img.getvalue())
    ctx.assets.insert_upload(
        asset_id="a1",
        media_type="image",
        file_path=stored.rel_path,
        mime_type="image/png",
        size_bytes=stored.size_bytes,
        width=4,
        height=4,
    )

    ctx.settings.set_str("google_api_key", "x")

    ctx.jobs.create(
        job_id="j1",
        job_type="image.generate",
        model_id="nano-banana-pro",
        auth_mode="api_key",
        params={
            "prompt": "x",
            "aspect_ratio": "1:1",
            "image_size": "1k",
            "reference_image_asset_id": "a1",
        },
    )

    runner = JobRunner(ctx, provider=(provider := _DummyProviderApiKey()), concurrency=1)
    runner._run_one("j1")

    job = ctx.jobs.get("j1")
    assert job is not None
    assert job["status"] == "succeeded"
    assert provider.last_provider_model == "gemini-3-pro-image-preview"
    assert provider.last_had_reference is True
