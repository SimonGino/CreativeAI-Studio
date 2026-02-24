import pytest

from creativeai_studio.providers.google_provider import GoogleProvider


class _DummyInlineData:
    def __init__(self, *, data: bytes, mime_type: str):
        self.data = data
        self.mime_type = mime_type


class _DummyPart:
    def __init__(self):
        self.inline_data = _DummyInlineData(data=b"img", mime_type="image/png")


class _DummyContent:
    def __init__(self):
        self.parts = [_DummyPart()]


class _DummyCandidate:
    def __init__(self):
        self.content = _DummyContent()


class _DummyResponse:
    def __init__(self):
        self.candidates = [_DummyCandidate()]


class _DummyModels:
    def __init__(self):
        self.last_contents = None

    def generate_content(self, *, model, contents, config):  # noqa: ARG002
        self.last_contents = contents
        return _DummyResponse()


class _DummyClient:
    def __init__(self):
        self.models = _DummyModels()


def test_google_provider_generate_image_with_reference_does_not_raise():
    dummy_client = _DummyClient()
    provider = GoogleProvider(client_factory=lambda **_: dummy_client)

    try:
        out = provider.generate_image(
            provider_model="gemini-3-pro-image-preview",
            prompt="x",
            aspect_ratio="1:1",
            image_size="1k",
            reference_image_bytes=b"ref",
            reference_image_mime_type="image/png",
            client=dummy_client,
        )
    except Exception as e:  # noqa: BLE001
        pytest.fail(f"generate_image raised {type(e).__name__}: {e}")

    assert out["mime_type"] == "image/png"
    assert out["bytes"] == b"img"
    assert isinstance(dummy_client.models.last_contents, list)
    assert len(dummy_client.models.last_contents) == 2
