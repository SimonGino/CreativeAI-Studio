from fastapi.testclient import TestClient

from creativeai_studio.config import AppConfig
from creativeai_studio.main import create_app


def test_put_and_get_default_auth(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    client = TestClient(app)

    put = client.put("/api/settings", json={"default_auth_mode": "vertex"})
    assert put.status_code == 200
    got = client.get("/api/settings")
    assert got.json()["default_auth_mode"] == "vertex"

