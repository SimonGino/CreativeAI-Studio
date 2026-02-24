from fastapi.testclient import TestClient

from creativeai_studio.config import AppConfig
from creativeai_studio.main import create_app


def test_clone_job_enqueues_new_job(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    enqueued: list[str] = []
    app.state.runner.enqueue = lambda job_id: enqueued.append(job_id)  # type: ignore[method-assign]
    client = TestClient(app)

    create_resp = client.post(
        "/api/jobs",
        json={
            "job_type": "video.generate",
            "model_id": "veo-3.1-fast",
            "params": {
                "prompt": "make it move",
                "duration_seconds": 4,
                "aspect_ratio": "16:9",
            },
            "auth": {"mode": "api_key"},
        },
    )
    assert create_resp.status_code == 200
    src_job = create_resp.json()

    clone_resp = client.post(f"/api/jobs/{src_job['id']}/clone", json={})
    assert clone_resp.status_code == 200
    clone_job = clone_resp.json()

    assert len(enqueued) == 2
    assert enqueued[0] == src_job["id"]
    assert enqueued[1] == clone_job["id"]
    assert clone_job["status"] == "queued"
    assert clone_job["job_type"] == "video.generate"
