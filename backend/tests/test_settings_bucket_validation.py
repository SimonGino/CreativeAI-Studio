from fastapi.testclient import TestClient

from creativeai_studio.config import AppConfig
from creativeai_studio.main import create_app


def test_bucket_rejects_gs_prefix(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    client = TestClient(app)
    resp = client.put("/api/settings", json={"vertex_gcs_bucket": "gs://abc"})
    assert resp.status_code == 400

