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

