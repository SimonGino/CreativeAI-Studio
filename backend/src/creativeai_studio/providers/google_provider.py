from __future__ import annotations

from typing import Any, Callable

from creativeai_studio.providers.nano_banana_provider import NanoBananaProvider
from creativeai_studio.providers.veo_provider import VeoProvider


class GoogleProvider:
    def __init__(
        self,
        client_factory: Callable[..., Any],
        *,
        nano_banana_provider: Any | None = None,
        veo_provider: Any | None = None,
    ):
        self._client_factory = client_factory
        self._nano_banana_provider = nano_banana_provider or NanoBananaProvider(client_factory=client_factory)
        self._veo_provider = veo_provider or VeoProvider(client_factory=client_factory)

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
        sequential_image_generation: str | None = None,
        sequential_image_generation_options: dict[str, Any] | None = None,
        watermark: bool | None = None,
        client: Any | None = None,
    ) -> dict[str, Any]:
        return self._nano_banana_provider.generate_image(
            provider_model=provider_model,
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            image_size=image_size,
            reference_image_bytes=reference_image_bytes,
            reference_image_mime_type=reference_image_mime_type,
            reference_images=reference_images,
            sequential_image_generation=sequential_image_generation,
            sequential_image_generation_options=sequential_image_generation_options,
            watermark=watermark,
            client=client,
        )

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
        return self._veo_provider.generate_video(
            provider_model=provider_model,
            prompt=prompt,
            duration_seconds=duration_seconds,
            aspect_ratio=aspect_ratio,
            start_image=start_image,
            end_image=end_image,
            client=client,
            poll_interval_seconds=poll_interval_seconds,
            max_polls=max_polls,
        )
