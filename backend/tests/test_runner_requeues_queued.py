from creativeai_studio.config import AppConfig
from creativeai_studio.main import create_app


def test_recover_enqueues_queued_and_fails_running(tmp_path):
    cfg = AppConfig(data_dir=tmp_path / "data")
    app = create_app(cfg)
    ctx = app.state.ctx

    ctx.jobs.create(
        job_id="j1",
        job_type="image.generate",
        model_id="nano-banana-pro",
        auth_mode="api_key",
        params={"prompt": "x", "aspect_ratio": "1:1", "image_size": "1k"},
    )

    ctx.jobs.create(
        job_id="j2",
        job_type="image.generate",
        model_id="nano-banana-pro",
        auth_mode="api_key",
        params={"prompt": "y", "aspect_ratio": "1:1", "image_size": "1k"},
    )
    ctx.jobs.set_status("j2", "running")

    runner = app.state.runner
    runner.recover_on_startup()

    assert runner.qsize() >= 1
    assert ctx.jobs.get("j2")["status"] == "failed"

