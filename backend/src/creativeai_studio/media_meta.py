from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image


def read_image_size(path: Path) -> Tuple[int, int]:
    with Image.open(path) as img:
        return img.size


def read_video_meta_ffprobe(path: Path) -> tuple[Optional[int], Optional[int], Optional[float]]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        str(path),
    ]
    out = subprocess.check_output(cmd)
    data = json.loads(out)

    duration = None
    try:
        duration = float(data.get("format", {}).get("duration"))
    except Exception:
        duration = None

    width = height = None
    for s in data.get("streams", []):
        if s.get("codec_type") == "video":
            width = s.get("width")
            height = s.get("height")
            break

    return width, height, duration

