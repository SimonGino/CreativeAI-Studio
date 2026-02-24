from unittest.mock import Mock

from creativeai_studio.providers.google_provider import GoogleProvider


def test_generate_image_returns_bytes():
    fake_client = Mock()
    fake_client.models.generate_images.return_value = Mock(
        generated_images=[Mock(image=Mock(image_bytes=b"img", mime_type="image/png"))]
    )
    p = GoogleProvider(client_factory=lambda **_: fake_client, gcs=None)
    out = p.generate_image(
        provider_model="imagen-3.0-generate-002",
        prompt="x",
        aspect_ratio="1:1",
        image_size="1k",
    )
    assert out["mime_type"] == "image/png"
    assert out["bytes"] == b"img"

