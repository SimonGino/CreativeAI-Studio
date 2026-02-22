import logging

from app.providers import get_provider
from app.utils.file_storage import save_media

logger = logging.getLogger(__name__)


async def generate_images(
    prompt: str,
    model: str,
    aspect_ratio: str = "1:1",
    number_of_images: int = 1,
    api_key: str | None = None,
    auth_type: str = "gemini",
) -> list[str]:
    """Generate images and return list of media URLs."""
    provider = get_provider(auth_type, api_key)
    result = await provider.generate_image(prompt, model, aspect_ratio, number_of_images)

    urls = []
    for img_bytes in result.images:
        url = await save_media(img_bytes, "png")
        urls.append(url)

    return urls
