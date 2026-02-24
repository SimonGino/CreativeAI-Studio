from fastapi.testclient import TestClient

from creativeai_studio.config import AppConfig
from creativeai_studio.main import create_app


def test_models_has_expected_ids(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    client = TestClient(app)
    resp = client.get("/api/models")
    assert resp.status_code == 200
    models = resp.json()
    ids = {m["model_id"] for m in models}
    assert {"nano-banana-pro", "veo-3.1", "veo-3.1-fast"} <= ids

    nano = next(m for m in models if m["model_id"] == "nano-banana-pro")
    assert nano["display_name"]
    assert nano["provider_id"] == "google"
    assert nano["provider_models"]["image_generate"] == "gemini-3-pro-image-preview"
