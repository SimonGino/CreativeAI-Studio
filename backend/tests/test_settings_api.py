from fastapi.testclient import TestClient

from creativeai_studio.config import AppConfig
from creativeai_studio.main import create_app


def test_put_and_get_default_auth(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    client = TestClient(app)

    put = client.put("/api/settings", json={"default_auth_mode": "api_key"})
    assert put.status_code == 200
    assert put.json()["default_auth_mode"] == "api_key"
    got = client.get("/api/settings")
    assert got.json()["default_auth_mode"] == "api_key"


def test_put_and_get_ark_api_key_presence(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    client = TestClient(app)

    put = client.put("/api/settings", json={"ark_api_key": "ark_xxx"})
    assert put.status_code == 200
    data = put.json()
    assert data["ark_api_key_present"] is True

    got = client.get("/api/settings")
    assert got.status_code == 200
    assert got.json()["ark_api_key_present"] is True
