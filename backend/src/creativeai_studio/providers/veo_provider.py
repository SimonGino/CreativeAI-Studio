from __future__ import annotations

import time
from typing import Any, Callable


class VeoProvider:
    def __init__(self, client_factory: Callable[..., Any]):
        self._client_factory = client_factory

    def generate_video(
        self,
        provider_model: str,
        prompt: str | None,
        duration_seconds: int,
        aspect_ratio: str,
        *,
        start_image: dict[str, Any] | None = None,
        end_image: dict[str, Any] | None = None,
        client: Any | None = None,
        poll_interval_seconds: float = 10.0,
        max_polls: int = 120,
    ) -> dict[str, Any]:
        from google.genai import types

        client = client or self._client_factory()

        source = types.GenerateVideosSource(prompt=prompt) if prompt else types.GenerateVideosSource()
        if start_image:
            source.image = types.Image(
                image_bytes=start_image["bytes"],
                mime_type=start_image.get("mime_type"),
            )

        config = types.GenerateVideosConfig(duration_seconds=int(duration_seconds), aspect_ratio=aspect_ratio)
        if end_image:
            config.last_frame = types.Image(
                image_bytes=end_image["bytes"],
                mime_type=end_image.get("mime_type"),
            )

        operation = client.models.generate_videos(model=provider_model, source=source, config=config)
        polls = 0
        while not operation.done:
            if polls >= max_polls:
                raise TimeoutError("Video generation timed out")
            if poll_interval_seconds:
                time.sleep(poll_interval_seconds)
            operation = client.operations.get(operation)
            polls += 1

        op_result = getattr(operation, "result", None) or getattr(operation, "response", None)
        generated_videos = getattr(op_result, "generated_videos", None) or []
        if not generated_videos:
            raise RuntimeError("No generated video output")

        generated_video = generated_videos[0]
        video = getattr(generated_video, "video", generated_video)
        video_bytes = getattr(video, "video_bytes", None)
        if not isinstance(video_bytes, (bytes, bytearray, memoryview)):
            downloaded_bytes = self._download_video_bytes_with_client(client=client, video=video)
            if downloaded_bytes is not None:
                return {"bytes": downloaded_bytes, "mime_type": getattr(video, "mime_type", "video/mp4")}

        if isinstance(video_bytes, (bytes, bytearray, memoryview)):
            return {"bytes": bytes(video_bytes), "mime_type": getattr(video, "mime_type", "video/mp4")}
        if getattr(video, "uri", None):
            return {"gcs_uri": video.uri, "mime_type": getattr(video, "mime_type", "video/mp4")}
        raise RuntimeError("No video output")

    @staticmethod
    def _download_video_bytes_with_client(*, client: Any, video: Any) -> bytes | None:
        files_api = getattr(client, "files", None)
        download = getattr(files_api, "download", None)
        if not callable(download):
            return None

        downloaded = download(file=video)
        if isinstance(downloaded, (bytes, bytearray, memoryview)):
            return bytes(downloaded)

        downloaded_bytes = getattr(downloaded, "video_bytes", None)
        if isinstance(downloaded_bytes, (bytes, bytearray, memoryview)):
            return bytes(downloaded_bytes)

        video_bytes = getattr(video, "video_bytes", None)
        if isinstance(video_bytes, (bytes, bytearray, memoryview)):
            return bytes(video_bytes)

        return None
