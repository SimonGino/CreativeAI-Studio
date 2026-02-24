from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from creativeai_studio.config import AppConfig
from creativeai_studio.main import create_app


def test_upload_image_and_fetch_content(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    client = TestClient(app)

    buf = BytesIO()
    Image.new("RGB", (32, 16), color=(0, 0, 0)).save(buf, format="PNG")
    buf.seek(0)

    up = client.post(
        "/api/assets/upload",
        files={"file": ("x.png", buf.read(), "image/png")},
    )
    assert up.status_code == 200
    asset_id = up.json()["id"]

    content = client.get(f"/api/assets/{asset_id}/content")
    assert content.status_code == 200
    assert content.headers["content-type"].startswith("image/")


def test_generated_asset_includes_source_model_info(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    client = TestClient(app)
    ctx = app.state.ctx

    ctx.jobs.create(
        job_id="j1",
        job_type="image.generate",
        model_id="nano-banana-pro",
        auth_mode="api_key",
        params={"prompt": "x"},
    )
    stored = ctx.asset_store.save_generated(asset_id="a1", ext=".png", content=b"png")
    ctx.assets.insert_generated(
        asset_id="a1",
        media_type="image",
        file_path=stored.rel_path,
        mime_type="image/png",
        size_bytes=stored.size_bytes,
        source_job_id="j1",
    )

    resp = client.get("/api/assets/a1")
    assert resp.status_code == 200
    asset = resp.json()
    assert asset["source_job_id"] == "j1"
    assert asset["source_model_id"] == "nano-banana-pro"
    assert asset["source_model_name"] == "Nano Banana Pro"

    listed = client.get("/api/assets").json()
    item = next(a for a in listed if a["id"] == "a1")
    assert item["source_model_id"] == "nano-banana-pro"
    assert item["source_model_name"] == "Nano Banana Pro"
