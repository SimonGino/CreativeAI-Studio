from creativeai_studio.db import Database


def test_db_init_creates_tables(tmp_path):
    db = Database(tmp_path / "app.db")
    db.init()
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    names = {r[0] for r in rows}
    assert {"settings", "assets", "jobs", "job_assets"} <= names
