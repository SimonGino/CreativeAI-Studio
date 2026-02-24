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
    assert {
        "nano-banana",
        "nano-banana-pro",
        "doubao-seedream-4-5-251128",
        "doubao-seedream-4-0-250828",
        "seedream-5-0-lite",
        "veo-3.1",
        "veo-3.1-fast",
        "seeddance-2-0",
    } <= ids

    nano_fast = next(m for m in models if m["model_id"] == "nano-banana")
    assert nano_fast["display_name"] == "Nano Banana"
    assert nano_fast["provider_id"] == "google"
    assert nano_fast["provider_models"]["image_generate"] == "gemini-2.5-flash-image"
    assert "4k" not in (nano_fast.get("resolution_presets") or [])

    nano = next(m for m in models if m["model_id"] == "nano-banana-pro")
    assert nano["display_name"]
    assert nano["provider_id"] == "google"
    assert nano["provider_models"]["image_generate"] == "gemini-3-pro-image-preview"
    assert "4k" in (nano.get("resolution_presets") or [])

    doubao = next(m for m in models if m["model_id"] == "doubao-seedream-4-5-251128")
    assert doubao["display_name"] == "Seedream-4.5"
    assert doubao["provider_id"] == "volcengine_ark"
    assert doubao["auth_support"] == ["api_key"]

    upcoming_image = next(m for m in models if m["model_id"] == "seedream-5-0-lite")
    assert upcoming_image["display_name"] == "Seedream 5.0 Lite"
    assert upcoming_image["coming_soon"] is True

    upcoming_video = next(m for m in models if m["model_id"] == "seeddance-2-0")
    assert upcoming_video["display_name"] == "SeedDance 2.0"
    assert upcoming_video["coming_soon"] is True
