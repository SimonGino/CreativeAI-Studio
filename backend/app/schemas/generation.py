from __future__ import annotations

from pydantic import BaseModel


class ImageGenerateRequest(BaseModel):
    prompt: str
    model: str = "gemini-2.5-flash-preview-image-generation"
    aspect_ratio: str = "1:1"  # 1:1, 3:4, 4:3, 9:16, 16:9
    number_of_images: int = 1
    # Auth override (optional, otherwise use server config)
    api_key: str | None = None
    auth_type: str = "gemini"  # gemini | vertex


class ImageGenerateResponse(BaseModel):
    images: list[str]  # media URLs
    model: str


class VideoGenerateRequest(BaseModel):
    prompt: str
    model: str = "veo-3.1-fast-generate-preview"
    aspect_ratio: str = "16:9"
    duration_seconds: int = 8  # 4, 6, 8
    resolution: str = "720p"  # 720p, 1080p
    generate_audio: bool = True
    image_url: str | None = None  # for image-to-video
    # Auth override
    api_key: str | None = None
    auth_type: str = "gemini"


class VideoGenerateResponse(BaseModel):
    task_id: str
    status: str


class VideoStatusResponse(BaseModel):
    task_id: str
    status: str  # pending | processing | completed | failed
    progress: float
    video_url: str | None = None
    error: str | None = None
