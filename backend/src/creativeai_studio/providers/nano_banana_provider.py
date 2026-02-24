from __future__ import annotations

from typing import Any, Callable


class NanoBananaProvider:
    def __init__(self, client_factory: Callable[..., Any]):
        self._client_factory = client_factory

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
                    image_size=(
                        image_size if provider_model == "gemini-3-pro-image-preview" else None
                    ),
                ),
            ),
        )

        for p in self._iter_response_parts(resp):
            inline = getattr(p, "inline_data", None)
            mime_type = getattr(inline, "mime_type", "") if inline is not None else ""
            if (
                inline
                and getattr(inline, "data", None)
                and isinstance(mime_type, str)
                and mime_type.startswith("image/")
            ):
                return {"bytes": inline.data, "mime_type": inline.mime_type}

        raise RuntimeError(self._no_image_output_message(resp))

    @staticmethod
    def _iter_response_parts(resp: Any):
        parts = getattr(resp, "parts", None)
        if parts is not None and not isinstance(parts, (str, bytes, bytearray)):
            try:
                iterator = iter(parts)
            except TypeError:
                iterator = None
            if iterator is not None:
                for p in iterator:
                    yield p

        for c in getattr(resp, "candidates", None) or []:
            for p in (c.content.parts if c.content else []) or []:
                yield p

    @classmethod
    def _no_image_output_message(cls, resp: Any) -> str:
        details: list[str] = []

        prompt_feedback = getattr(resp, "prompt_feedback", None)
        if prompt_feedback is not None:
            block_reason_message = getattr(prompt_feedback, "block_reason_message", None)
            if block_reason_message:
                details.append(f"prompt_feedback={block_reason_message}")
            block_reason = getattr(prompt_feedback, "block_reason", None)
            if block_reason:
                details.append(f"block_reason={block_reason}")

        for idx, candidate in enumerate(getattr(resp, "candidates", None) or []):
            finish_reason = getattr(candidate, "finish_reason", None)
            finish_message = getattr(candidate, "finish_message", None)
            if finish_reason:
                details.append(f"candidate[{idx}].finish_reason={finish_reason}")
            if finish_message:
                details.append(f"candidate[{idx}].finish_message={finish_message}")

        text_snippets: list[str] = []
        for p in cls._iter_response_parts(resp):
            text = getattr(p, "text", None)
            if isinstance(text, str):
                t = " ".join(text.split())
                if t:
                    text_snippets.append(t[:160])
            if len(text_snippets) >= 2:
                break
        if text_snippets:
            details.append("text=" + " | ".join(text_snippets))

        if not details:
            return "No image output"
        return "No image output (" + "; ".join(details) + ")"

    @staticmethod
    def _normalize_image_size(image_size: str) -> str:
        v = str(image_size or "").strip()
        if not v:
            return v
        if v.lower() in {"1k", "2k", "4k"}:
            return v.upper()
        return v
