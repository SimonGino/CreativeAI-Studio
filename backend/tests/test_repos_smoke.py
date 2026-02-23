from creativeai_studio.db import Database
from creativeai_studio.repositories.assets_repo import AssetsRepo
from creativeai_studio.repositories.jobs_repo import JobsRepo
from creativeai_studio.repositories.settings_repo import SettingsRepo


def test_repos_roundtrip(tmp_path):
    db = Database(tmp_path / "app.db")
    db.init()
    settings = SettingsRepo(db)
    assets = AssetsRepo(db)
    jobs = JobsRepo(db)

    settings.set_str("google_api_key", "x")
    assert settings.get_str("google_api_key") == "x"

    a = assets.insert_upload(
        asset_id="a1",
        media_type="image",
        file_path="assets/uploads/a1.png",
        mime_type="image/png",
        size_bytes=1,
    )
    assert a["id"] == "a1"

    j = jobs.create(
        job_id="j1",
        job_type="image.generate",
        model_id="nano-banana-pro",
        auth_mode="api_key",
        params={"prompt": "x"},
    )
    assert j["id"] == "j1"

