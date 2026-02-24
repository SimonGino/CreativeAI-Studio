from fastapi.testclient import TestClient

from creativeai_studio.config import AppConfig
from creativeai_studio.main import create_app


def test_video_extend_is_disabled_after_vertex_removal(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    client = TestClient(app)

    resp = client.post(
        "/api/jobs",
        json={
            "job_type": "video.extend",
            "model_id": "veo-3.1",
            "params": {"input_video_asset_id": "x", "extend_seconds": 5},
        },
    )
    assert resp.status_code == 400
    assert "video.extend is disabled" in resp.text


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


def test_reference_image_ids_normalized_for_image_generate(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    client = TestClient(app)

    resp = client.post(
        "/api/jobs",
        json={
            "job_type": "image.generate",
            "model_id": "doubao-seedream-4-5-251128",
            "params": {
                "prompt": "x",
                "reference_image_asset_id": "a1",
                "reference_image_asset_ids": ["a2"],
                "image_size": "2k",
                "sequential_image_generation": "auto",
                "sequential_image_generation_options": {"max_images": 3},
            },
            "auth": {"mode": "api_key"},
        },
    )
    assert resp.status_code == 200
    params = resp.json()["params"]
    assert params["reference_image_asset_ids"] == ["a1", "a2"]
    assert params["reference_image_asset_id"] == "a1"
    assert params["sequential_image_generation_options"]["max_images"] == 3


def test_google_model_rejects_multiple_reference_images(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    client = TestClient(app)

    resp = client.post(
        "/api/jobs",
        json={
            "job_type": "image.generate",
            "model_id": "nano-banana-pro",
            "params": {
                "prompt": "x",
                "reference_image_asset_ids": ["a1", "a2"],
                "aspect_ratio": "1:1",
                "image_size": "1k",
            },
            "auth": {"mode": "api_key"},
        },
    )
    assert resp.status_code == 400
    assert "reference_image count exceeds max 1" in resp.text


def test_doubao_rejects_reference_plus_max_images_over_total_limit(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    client = TestClient(app)

    resp = client.post(
        "/api/jobs",
        json={
            "job_type": "image.generate",
            "model_id": "doubao-seedream-4-5-251128",
            "params": {
                "prompt": "x",
                "reference_image_asset_ids": [f"a{i}" for i in range(1, 12)],
                "image_size": "2k",
                "sequential_image_generation": "auto",
                "sequential_image_generation_options": {"max_images": 5},
            },
            "auth": {"mode": "api_key"},
        },
    )
    assert resp.status_code == 400
    assert "reference_image count + max_images exceeds 15" in resp.text


def test_seedream_45_rejects_unsupported_1k_size(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    client = TestClient(app)

    resp = client.post(
        "/api/jobs",
        json={
            "job_type": "image.generate",
            "model_id": "doubao-seedream-4-5-251128",
            "params": {
                "prompt": "x",
                "image_size": "1k",
                "aspect_ratio": "1:1",
            },
            "auth": {"mode": "api_key"},
        },
    )
    assert resp.status_code == 400
    assert "image_size not supported" in resp.text


def test_seedream_45_accepts_2k_size(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    client = TestClient(app)

    resp = client.post(
        "/api/jobs",
        json={
            "job_type": "image.generate",
            "model_id": "doubao-seedream-4-5-251128",
            "params": {
                "prompt": "x",
                "image_size": "2k",
                "aspect_ratio": "1:1",
            },
            "auth": {"mode": "api_key"},
        },
    )
    assert resp.status_code == 200


def test_vertex_auth_mode_is_rejected(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    client = TestClient(app)

    resp = client.post(
        "/api/jobs",
        json={
            "job_type": "image.generate",
            "model_id": "nano-banana-pro",
            "params": {
                "prompt": "x",
                "image_size": "2k",
                "aspect_ratio": "1:1",
            },
            "auth": {"mode": "vertex"},
        },
    )
    assert resp.status_code == 400
    assert "Vertex AI auth mode has been removed" in resp.text


def test_coming_soon_model_is_rejected(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    client = TestClient(app)

    resp = client.post(
        "/api/jobs",
        json={
            "job_type": "image.generate",
            "model_id": "seedream-5-0-lite",
            "params": {
                "prompt": "x",
                "image_size": "2k",
                "aspect_ratio": "1:1",
            },
            "auth": {"mode": "api_key"},
        },
    )
    assert resp.status_code == 400
    assert "coming soon" in resp.text.lower()


def test_veo_31_fast_rejects_unsupported_duration_and_aspect_ratio(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    client = TestClient(app)

    resp = client.post(
        "/api/jobs",
        json={
            "job_type": "video.generate",
            "model_id": "veo-3.1-fast",
            "params": {
                "prompt": "x",
                "duration_seconds": 4,
                "aspect_ratio": "1:1",
            },
            "auth": {"mode": "api_key"},
        },
    )
    assert resp.status_code == 400
    assert "aspect_ratio not supported" in resp.text

    resp = client.post(
        "/api/jobs",
        json={
            "job_type": "video.generate",
            "model_id": "veo-3.1-fast",
            "params": {
                "prompt": "x",
                "duration_seconds": 5,
                "aspect_ratio": "16:9",
            },
            "auth": {"mode": "api_key"},
        },
    )
    assert resp.status_code == 400
    assert "duration_seconds not supported" in resp.text
