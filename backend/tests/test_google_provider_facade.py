from creativeai_studio.providers.google_provider import GoogleProvider


class _FakeNanoBananaProvider:
    def __init__(self):
        self.calls = []

    def generate_image(self, **kwargs):
        self.calls.append(kwargs)
        return {"bytes": b"img", "mime_type": "image/png"}


class _FakeVeoProvider:
    def __init__(self):
        self.calls = []

    def generate_video(self, **kwargs):
        self.calls.append(kwargs)
        return {"gcs_uri": "gs://bucket/out.mp4", "mime_type": "video/mp4"}


def test_google_provider_delegates_image_generation_to_nano_banana_provider():
    image_provider = _FakeNanoBananaProvider()
    video_provider = _FakeVeoProvider()
    provider = GoogleProvider(
        client_factory=lambda **_: object(),
        nano_banana_provider=image_provider,
        veo_provider=video_provider,
    )

    out = provider.generate_image(
        provider_model="gemini-3-pro-image-preview",
        prompt="draw",
        aspect_ratio="1:1",
        image_size="1k",
        watermark=False,
    )

    assert out["mime_type"] == "image/png"
    assert len(image_provider.calls) == 1
    assert image_provider.calls[0]["provider_model"] == "gemini-3-pro-image-preview"
    assert image_provider.calls[0]["prompt"] == "draw"
    assert image_provider.calls[0]["aspect_ratio"] == "1:1"
    assert image_provider.calls[0]["image_size"] == "1k"
    assert image_provider.calls[0]["watermark"] is False
    assert not video_provider.calls


def test_google_provider_delegates_video_generation_to_veo_provider():
    image_provider = _FakeNanoBananaProvider()
    video_provider = _FakeVeoProvider()
    provider = GoogleProvider(
        client_factory=lambda **_: object(),
        nano_banana_provider=image_provider,
        veo_provider=video_provider,
    )

    out = provider.generate_video(
        provider_model="veo-3.1-generate-preview",
        prompt="video",
        duration_seconds=4,
        aspect_ratio="16:9",
    )

    assert out["mime_type"] == "video/mp4"
    assert len(video_provider.calls) == 1
    assert video_provider.calls[0]["provider_model"] == "veo-3.1-generate-preview"
    assert video_provider.calls[0]["prompt"] == "video"
    assert video_provider.calls[0]["duration_seconds"] == 4
    assert video_provider.calls[0]["aspect_ratio"] == "16:9"
    assert not image_provider.calls
