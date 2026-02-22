from __future__ import annotations

import base64
import logging

from google import genai
from google.genai import types

from app.providers.base import ImageProvider, ImageResult, VideoProvider, VideoStatus

logger = logging.getLogger(__name__)


class GeminiAPIProvider(ImageProvider, VideoProvider):
    """Provider using Gemini API with API Key authentication."""

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    async def generate_image(
        self,
        prompt: str,
        model: str = "gemini-2.5-flash-preview-image-generation",
        aspect_ratio: str = "1:1",
        number_of_images: int = 1,
    ) -> ImageResult:
        # Gemini native image generation uses generateContent
        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            ),
        )

        images = []
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                images.append(part.inline_data.data)

        if not images:
            raise ValueError("No images generated")

        return ImageResult(images=images)

    async def start_video_generation(
        self,
        prompt: str,
        model: str = "veo-3.1-fast-generate-preview",
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8,
        resolution: str = "720p",
        generate_audio: bool = True,
        image_data: bytes | None = None,
    ) -> str:
        config = types.GenerateVideosConfig(
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            duration_seconds=duration_seconds,
            number_of_videos=1,
            person_generation="allow_adult",
        )

        kwargs: dict = {"model": model, "prompt": prompt, "config": config}

        if image_data:
            kwargs["image"] = types.Image(
                image_bytes=image_data,
                mime_type="image/png",
            )

        operation = self.client.models.generate_videos(**kwargs)
        return operation.name

    async def poll_video_status(self, operation_id: str) -> VideoStatus:
        operation = self.client.operations.get(operation_id)

        if not operation.done:
            # Estimate progress from metadata if available
            return VideoStatus(done=False, progress=0.5)

        if hasattr(operation, "error") and operation.error:
            return VideoStatus(done=True, error=str(operation.error))

        # Download video
        video = operation.response.generated_videos[0]
        video_data = self.client.files.download(file=video.video)
        return VideoStatus(done=True, progress=1.0, video_bytes=video_data)
