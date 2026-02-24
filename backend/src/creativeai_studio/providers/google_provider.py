from __future__ import annotations

import time
from typing import Any, Callable


class GoogleProvider:
    def __init__(self, client_factory: Callable[..., Any]):
        self._client_factory = client_factory

    def make_client_api_key(self, api_key: str):
        return self._client_factory(api_key=api_key)

    def generate_image(
        self,
        provider_model: str,
        prompt: str,
        aspect_ratio: str,
        image_size: str,
        *,
        reference_image_bytes: bytes | None = None,
        reference_image_mime_type: str | None = None,
        reference_images: list[dict[str, Any]] | None = None,
        sequential_image_generation: str | None = None,  # noqa: ARG002
        sequential_image_generation_options: dict[str, Any] | None = None,  # noqa: ARG002
        watermark: bool | None = None,  # noqa: ARG002
        client: Any | None = None,
    ) -> dict[str, Any]:
        image_size = self._normalize_image_size(image_size)
        if reference_images and reference_image_bytes is None:
            first = reference_images[0]
            reference_image_bytes = first.get("bytes")
            reference_image_mime_type = first.get("mime_type")
        if reference_image_bytes is not None and not provider_model.startswith("gemini"):
            raise RuntimeError("reference_image not supported for provider model")
        if provider_model.startswith("gemini"):
            return self._generate_image_by_gemini(
                provider_model=provider_model,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                image_size=image_size,
                reference_image_bytes=reference_image_bytes,
                reference_image_mime_type=reference_image_mime_type,
                client=client,
            )

        client = client or self._client_factory()
        resp = client.models.generate_images(
            model=provider_model,
            prompt=prompt,
            config={"aspect_ratio": aspect_ratio, "image_size": image_size},
        )
        img = resp.generated_images[0].image
        return {"bytes": img.image_bytes, "mime_type": img.mime_type}

    def _generate_image_by_gemini(
        self,
        *,
        provider_model: str,
        prompt: str,
        aspect_ratio: str,
        image_size: str,
        reference_image_bytes: bytes | None,
        reference_image_mime_type: str | None,
        client: Any | None,
    ) -> dict[str, Any]:
        from google.genai import types

        client = client or self._client_factory()
        contents: Any
        if reference_image_bytes is None:
            contents = prompt
        else:
            contents = [
                types.Part.from_text(text=prompt),
                types.Part.from_bytes(
                    data=reference_image_bytes,
                    mime_type=str(reference_image_mime_type or "image/png"),
                ),
            ]
        resp = client.models.generate_content(
            model=provider_model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    image_size=image_size,
                ),
            ),
        )

        for c in resp.candidates or []:
            for p in (c.content.parts if c.content else []) or []:
                inline = getattr(p, "inline_data", None)
                if inline and getattr(inline, "data", None) and getattr(inline, "mime_type", "").startswith(
                    "image/"
                ):
                    return {"bytes": inline.data, "mime_type": inline.mime_type}

        raise RuntimeError("No image output")

    @staticmethod
    def _normalize_image_size(image_size: str) -> str:
        v = str(image_size or "").strip()
        if not v:
            return v
        if v.lower() in {"1k", "2k", "4k"}:
            return v.upper()
        return v

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

        video = operation.result.generated_videos[0].video
        video_bytes = getattr(video, "video_bytes", None)
        if isinstance(video_bytes, (bytes, bytearray, memoryview)):
            return {"bytes": bytes(video_bytes), "mime_type": getattr(video, "mime_type", "video/mp4")}
        if getattr(video, "uri", None):
            return {"gcs_uri": video.uri, "mime_type": getattr(video, "mime_type", "video/mp4")}
        raise RuntimeError("No video output")
