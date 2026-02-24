from __future__ import annotations

import base64
from typing import Any, Callable


class VolcengineArkProvider:
    def __init__(
        self,
        client_factory: Callable[..., Any],
        *,
        base_url: str = "https://ark.cn-beijing.volces.com/api/v3",
    ):
        self._client_factory = client_factory
        self._base_url = base_url.rstrip("/")

    def make_client_api_key(self, api_key: str):
        return self._client_factory(base_url=self._base_url, api_key=api_key)

    def generate_image(
        self,
        provider_model: str,
        prompt: str,
        aspect_ratio: str,  # noqa: ARG002
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
        client = client or self._client_factory(base_url=self._base_url)

        refs = self._coerce_reference_images(
            reference_image_bytes=reference_image_bytes,
            reference_image_mime_type=reference_image_mime_type,
            reference_images=reference_images,
        )

        extra_body: dict[str, Any] = {}
        if refs:
            extra_body["image"] = refs[0] if len(refs) == 1 else refs
        if sequential_image_generation in {"disabled", "auto"}:
            extra_body["sequential_image_generation"] = sequential_image_generation
        if (
            isinstance(sequential_image_generation_options, dict)
            and sequential_image_generation_options.get("max_images") is not None
        ):
            extra_body["sequential_image_generation_options"] = {
                "max_images": int(sequential_image_generation_options["max_images"])
            }
        if watermark is not None:
            extra_body["watermark"] = bool(watermark)

        kwargs: dict[str, Any] = {
            "model": provider_model,
            "prompt": prompt,
            "size": self._normalize_size(image_size),
            "response_format": "url",
        }
        if extra_body:
            kwargs["extra_body"] = extra_body

        resp = client.images.generate(**kwargs)
        items: list[dict[str, Any]] = []
        for item in getattr(resp, "data", []) or []:
            url = getattr(item, "url", None)
            if url:
                items.append({"url": str(url)})
                continue
            b64_json = getattr(item, "b64_json", None)
            if b64_json:
                items.append({"b64_json": str(b64_json)})
                continue
            if isinstance(item, dict):
                if item.get("url"):
                    items.append({"url": str(item["url"])})
                    continue
                if item.get("b64_json"):
                    items.append({"b64_json": str(item["b64_json"])})
                    continue

        if not items:
            raise RuntimeError("No image output")
        return {"items": items}

    def generate_image_text(
        self,
        *,
        provider_model: str,
        prompt: str,
        image_size: str,
        client: Any | None = None,
        watermark: bool | None = None,
    ) -> dict[str, Any]:
        return self.generate_image(
            provider_model=provider_model,
            prompt=prompt,
            aspect_ratio="1:1",
            image_size=image_size,
            client=client,
            watermark=watermark,
        )

    def generate_image_with_reference(
        self,
        *,
        provider_model: str,
        prompt: str,
        image_size: str,
        reference_image_bytes: bytes,
        reference_image_mime_type: str,
        client: Any | None = None,
        watermark: bool | None = None,
    ) -> dict[str, Any]:
        return self.generate_image(
            provider_model=provider_model,
            prompt=prompt,
            aspect_ratio="1:1",
            image_size=image_size,
            reference_image_bytes=reference_image_bytes,
            reference_image_mime_type=reference_image_mime_type,
            client=client,
            watermark=watermark,
        )

    def generate_image_with_references(
        self,
        *,
        provider_model: str,
        prompt: str,
        image_size: str,
        reference_images: list[dict[str, Any]],
        client: Any | None = None,
        watermark: bool | None = None,
        sequential_image_generation: str | None = None,
        sequential_image_generation_options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.generate_image(
            provider_model=provider_model,
            prompt=prompt,
            aspect_ratio="1:1",
            image_size=image_size,
            reference_images=reference_images,
            client=client,
            watermark=watermark,
            sequential_image_generation=sequential_image_generation,
            sequential_image_generation_options=sequential_image_generation_options,
        )

    @staticmethod
    def _normalize_size(image_size: str) -> str:
        v = str(image_size or "1K").strip()
        if not v:
            return "1K"
        if v.lower() in {"1k", "2k"}:
            return v.upper()
        return v

    @classmethod
    def _coerce_reference_images(
        cls,
        *,
        reference_image_bytes: bytes | None,
        reference_image_mime_type: str | None,
        reference_images: list[dict[str, Any]] | None,
    ) -> list[str]:
        refs: list[str] = []
        if reference_images:
            for ref in reference_images:
                data = ref.get("bytes")
                if not isinstance(data, (bytes, bytearray, memoryview)):
                    continue
                mime_type = str(ref.get("mime_type") or "image/png")
                refs.append(cls._to_data_url(bytes(data), mime_type))
        if reference_image_bytes is not None and not refs:
            refs.append(cls._to_data_url(reference_image_bytes, str(reference_image_mime_type or "image/png")))
        return refs

    @staticmethod
    def _to_data_url(data: bytes, mime_type: str) -> str:
        encoded = base64.b64encode(data).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"
