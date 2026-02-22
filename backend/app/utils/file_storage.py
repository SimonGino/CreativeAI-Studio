import os
import uuid

import aiofiles

from app.config import settings


async def save_media(data: bytes, extension: str = "png") -> str:
    """Save media bytes to disk, return relative URL path."""
    filename = f"{uuid.uuid4().hex[:16]}.{extension}"
    filepath = os.path.join(settings.media_dir, filename)
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(data)
    return f"/media/{filename}"
