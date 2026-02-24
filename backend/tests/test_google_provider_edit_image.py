from unittest.mock import Mock

from creativeai_studio.providers.google_provider import GoogleProvider


def test_edit_image_returns_bytes():
    fake_client = Mock()
    fake_client.models.edit_image.return_value = Mock(
        generated_images=[Mock(image=Mock(image_bytes=b"img", mime_type="image/png"))]
    )
    p = GoogleProvider(client_factory=lambda **_: fake_client, gcs=None)
    out = p.edit_image(
        provider_model="imagen-3.0-capability-001",
        prompt="x",
        reference_image_bytes=b"ref",
        reference_image_mime_type="image/png",
        aspect_ratio="1:1",
        client=fake_client,
    )
    assert out["mime_type"] == "image/png"
    assert out["bytes"] == b"img"

