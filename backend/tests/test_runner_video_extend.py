from creativeai_studio.config import AppConfig
from creativeai_studio.main import create_app
from creativeai_studio.runner import JobRunner


class _DummyProvider:
    def make_client_vertex(self, **_):
        return object()

    def __init__(self):
        self.last_provider_model: str | None = None

    def extend_video(self, *, provider_model: str, **__):
        self.last_provider_model = provider_model
        return {"bytes": b"out", "mime_type": "video/mp4"}


class _DummyGcs:
    def upload_file(self, bucket: str, object_name: str, local_path):  # noqa: ARG002
        return f"gs://{bucket}/{object_name}"


def test_runner_video_extend_creates_child_asset(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    ctx = app.state.ctx

    stored = ctx.asset_store.save_upload(asset_id="a1", filename="in.mp4", content=b"in")
    ctx.assets.insert_upload(
        asset_id="a1",
        media_type="video",
        file_path=stored.rel_path,
        mime_type="video/mp4",
        size_bytes=stored.size_bytes,
    )

    ctx.settings.set_str("vertex_sa_path", str(ctx.cfg.data_dir / "credentials" / "vertex-sa.json"))
    ctx.settings.set_str("vertex_project_id", "p")
    ctx.settings.set_str("vertex_location", "us-central1")
    ctx.settings.set_str("vertex_gcs_bucket", "b")

    ctx.jobs.create(
        job_id="j1",
        job_type="video.extend",
        model_id="veo-3.1",
        auth_mode="vertex",
        params={"input_video_asset_id": "a1", "extend_seconds": 5, "prompt": "x"},
    )

    runner = JobRunner(
        ctx,
        provider=(provider := _DummyProvider()),
        gcs=_DummyGcs(),
        vertex_credentials_factory=lambda _: object(),
        concurrency=1,
    )
    runner._run_one("j1")

    job = ctx.jobs.get("j1")
    assert job is not None
    assert job["status"] == "succeeded"
    assert provider.last_provider_model == "veo-3.1"

    out_id = job["result"]["output_asset_id"]
    asset = ctx.assets.get(out_id)
    assert asset is not None
    assert asset["parent_asset_id"] == "a1"
