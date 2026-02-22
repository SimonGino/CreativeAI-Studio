from __future__ import annotations

import logging

from google.auth.transport.requests import Request
from google.oauth2 import service_account
import httpx

from app.providers.base import ImageProvider, ImageResult, VideoProvider, VideoStatus

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]


class VertexAIProvider(ImageProvider, VideoProvider):
    """Provider using Vertex AI with Service Account JSON authentication."""

    def __init__(self, service_account_json: str, location: str = "us-central1"):
        self.location = location
        self.credentials = service_account.Credentials.from_service_account_file(
            service_account_json, scopes=SCOPES
        )
        self.project_id = self.credentials.project_id
        self.base_url = f"https://{location}-aiplatform.googleapis.com/v1"

    def _get_token(self) -> str:
        if not self.credentials.valid:
            self.credentials.refresh(Request())
        return self.credentials.token

    def _model_endpoint(self, model: str) -> str:
        return f"{self.base_url}/projects/{self.project_id}/locations/{self.location}/publishers/google/models/{model}"

    async def generate_image(
        self,
        prompt: str,
        model: str = "gemini-2.5-flash-preview-image-generation",
        aspect_ratio: str = "1:1",
        number_of_images: int = 1,
    ) -> ImageResult:
        url = f"{self._model_endpoint(model)}:generateContent"
        headers = {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json",
        }
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
        }

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        images = []
        for part in data["candidates"][0]["content"]["parts"]:
            if "inlineData" in part and part["inlineData"]["mimeType"].startswith("image/"):
                import base64
                images.append(base64.b64decode(part["inlineData"]["data"]))

        if not images:
            raise ValueError("No images generated")

        return ImageResult(images=images)

    async def start_video_generation(
        self,
        prompt: str,
        model: str = "veo-3.1-fast-generate-001",
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8,
        resolution: str = "720p",
        generate_audio: bool = True,
        image_data: bytes | None = None,
    ) -> str:
        url = f"{self._model_endpoint(model)}:predictLongRunning"
        headers = {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json",
        }

        instance: dict = {"prompt": prompt}
        if image_data:
            import base64
            instance["image"] = {
                "bytesBase64Encoded": base64.b64encode(image_data).decode(),
                "mimeType": "image/png",
            }

        body = {
            "instances": [instance],
            "parameters": {
                "aspectRatio": aspect_ratio,
                "resolution": resolution,
                "durationSeconds": str(duration_seconds),
                "generateAudio": generate_audio,
                "sampleCount": 1,
                "personGeneration": "allow_adult",
            },
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        return data["name"]

    async def poll_video_status(self, operation_id: str) -> VideoStatus:
        url = f"{self.base_url}/{operation_id}"
        headers = {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        if not data.get("done", False):
            progress = data.get("metadata", {}).get("progressPercent", 50) / 100
            return VideoStatus(done=False, progress=progress)

        if "error" in data:
            return VideoStatus(done=True, error=data["error"].get("message", "Unknown error"))

        # Download video from GCS URI
        videos = data.get("response", {}).get("generateVideoResponse", {}).get("generatedSamples", [])
        if videos:
            video_uri = videos[0].get("video", {}).get("uri", "")
            if video_uri:
                async with httpx.AsyncClient(timeout=120) as client:
                    resp = await client.get(
                        video_uri,
                        headers={"Authorization": f"Bearer {self._get_token()}"},
                    )
                    return VideoStatus(done=True, progress=1.0, video_bytes=resp.content)

        return VideoStatus(done=True, error="No video in response")
