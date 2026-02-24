from fastapi.testclient import TestClient

from creativeai_studio.config import AppConfig
from creativeai_studio.main import create_app


def test_extend_requires_vertex_bucket(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    client = TestClient(app)

    resp = client.post(
        "/api/jobs",
        json={
            "job_type": "video.extend",
            "model_id": "veo-3.1",
            "params": {"input_video_asset_id": "x", "extend_seconds": 5},
            "auth": {"mode": "vertex"},
        },
    )
    assert resp.status_code == 400


def test_reference_image_allows_api_key(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    client = TestClient(app)

    resp = client.post(
        "/api/jobs",
        json={
            "job_type": "image.generate",
            "model_id": "nano-banana-pro",
            "prompt": "x",
            "params": {
                "reference_image_asset_id": "a1",
                "aspect_ratio": "1:1",
                "image_size": "1k",
            },
            "auth": {"mode": "api_key"},
        },
    )
    assert resp.status_code == 200
