from __future__ import annotations

import time
from typing import Any, Callable


class GoogleProvider:
    def __init__(self, client_factory: Callable[..., Any], gcs: Any | None):
        self._client_factory = client_factory
        self._gcs = gcs

    def make_client_api_key(self, api_key: str):
        return self._client_factory(api_key=api_key)

    def make_client_vertex(self, *, credentials: Any, project: str, location: str):
        return self._client_factory(vertexai=True, project=project, location=location, credentials=credentials)

    def generate_image(
        self,
        provider_model: str,
        prompt: str,
        aspect_ratio: str,
        image_size: str,
        *,
        reference_image_bytes: bytes | None = None,
        reference_image_mime_type: str | None = None,
        client: Any | None = None,
    ) -> dict[str, Any]:
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

    def edit_image(
        self,
        provider_model: str,
        prompt: str,
        reference_image_bytes: bytes,
        reference_image_mime_type: str,
        aspect_ratio: str,
        *,
        client: Any | None = None,
    ) -> dict[str, Any]:
        from google.genai import types

        client = client or self._client_factory()

        raw = types.RawReferenceImage(
            reference_id=1,
            reference_image=types.Image(
                image_bytes=reference_image_bytes,
                mime_type=reference_image_mime_type,
            ),
        )
        mask = types.MaskReferenceImage(
            reference_id=2,
            config=types.MaskReferenceConfig(mask_mode=types.MaskReferenceMode.MASK_MODE_BACKGROUND),
        )
        resp = client.models.edit_image(
            model=provider_model,
            prompt=prompt,
            reference_images=[raw, mask],
            config=types.EditImageConfig(number_of_images=1, aspect_ratio=aspect_ratio),
        )
        img = resp.generated_images[0].image
        return {"bytes": img.image_bytes, "mime_type": img.mime_type}

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

    def extend_video(
        self,
        provider_model: str,
        input_video_uri: str,
        extend_seconds: int,
        *,
        prompt: str | None = None,
        aspect_ratio: str | None = None,
        output_gcs_uri: str | None = None,
        client: Any | None = None,
        poll_interval_seconds: float = 10.0,
        max_polls: int = 240,
    ) -> dict[str, Any]:
        from google.genai import types

        client = client or self._client_factory()

        source = types.GenerateVideosSource(video=types.Video(uri=input_video_uri))
        if prompt:
            source.prompt = prompt

        config = types.GenerateVideosConfig(duration_seconds=int(extend_seconds))
        if aspect_ratio:
            config.aspect_ratio = aspect_ratio
        if output_gcs_uri:
            config.output_gcs_uri = output_gcs_uri

        operation = client.models.generate_videos(model=provider_model, source=source, config=config)
        polls = 0
        while not operation.done:
            if polls >= max_polls:
                raise TimeoutError("Video extend timed out")
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
