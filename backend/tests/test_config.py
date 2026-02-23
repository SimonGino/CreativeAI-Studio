from pathlib import Path

from creativeai_studio.config import AppConfig


def test_ensure_dirs(tmp_path: Path):
    cfg = AppConfig(data_dir=tmp_path / "data")
    cfg.ensure_dirs()
    assert (cfg.data_dir / "assets/uploads").exists()
    assert (cfg.data_dir / "assets/generated").exists()
    assert (cfg.data_dir / "credentials").exists()
    assert (cfg.data_dir / "tmp").exists()
