from fastapi.testclient import TestClient

from creativeai_studio.config import AppConfig
from creativeai_studio.main import create_app


def test_ctx_attached(tmp_path):
    cfg = AppConfig(data_dir=tmp_path / "data")
    app = create_app(cfg)
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert hasattr(app.state, "ctx")

