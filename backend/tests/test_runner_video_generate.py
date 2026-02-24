from creativeai_studio.config import AppConfig
from creativeai_studio.main import create_app
from creativeai_studio.runner import JobRunner


class _DummyProvider:
    def make_client_api_key(self, api_key: str):  # noqa: ARG002
        return object()

    def __init__(self):
        self.last_provider_model: str | None = None

    def generate_video(self, *, provider_model: str, **__):
        self.last_provider_model = provider_model
        return {"bytes": b"vid", "mime_type": "video/mp4"}


def test_runner_video_generate_stores_asset(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    ctx = app.state.ctx
    ctx.settings.set_str("google_api_key", "x")

    ctx.jobs.create(
        job_id="j1",
        job_type="video.generate",
        model_id="veo-3.1",
        auth_mode="api_key",
        params={"prompt": "x", "aspect_ratio": "16:9", "duration_seconds": 5},
    )

    provider = _DummyProvider()
    runner = JobRunner(ctx, provider=provider, concurrency=1)
    runner._run_one("j1")

    job = ctx.jobs.get("j1")
    assert job is not None
    assert job["status"] == "succeeded"
    assert provider.last_provider_model == "veo-3.1"
    assert job["result"]["output_asset_id"]

    asset = ctx.assets.get(job["result"]["output_asset_id"])
    assert asset is not None
    assert asset["media_type"] == "video"
    assert asset["mime_type"].startswith("video/")
