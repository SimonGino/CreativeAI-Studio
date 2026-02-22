from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ImageResult:
    images: list[bytes]  # raw image bytes
    mime_type: str = "image/png"


@dataclass
class VideoStatus:
    done: bool
    progress: float = 0.0
    video_bytes: bytes | None = None
    error: str | None = None


class ImageProvider(ABC):
    @abstractmethod
    async def generate_image(
        self,
        prompt: str,
        model: str,
        aspect_ratio: str = "1:1",
        number_of_images: int = 1,
    ) -> ImageResult: ...


class VideoProvider(ABC):
    @abstractmethod
    async def start_video_generation(
        self,
        prompt: str,
        model: str,
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8,
        resolution: str = "720p",
        generate_audio: bool = True,
        image_data: bytes | None = None,
    ) -> str:
        """Start video generation, return operation ID."""
        ...

    @abstractmethod
    async def poll_video_status(self, operation_id: str) -> VideoStatus: ...
