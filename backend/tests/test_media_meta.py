from pathlib import Path

from PIL import Image

from creativeai_studio.media_meta import read_image_size


def test_read_image_size(tmp_path: Path):
    p = tmp_path / "x.png"
    Image.new("RGB", (64, 32), color=(255, 0, 0)).save(p)
    w, h = read_image_size(p)
    assert (w, h) == (64, 32)

