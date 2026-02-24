from unittest.mock import Mock

from creativeai_studio.providers.google_provider import GoogleProvider


def test_generate_image_with_gemini_returns_bytes():
    fake_client = Mock()
    fake_client.models.generate_content.return_value = Mock(
        candidates=[
            Mock(
                content=Mock(
                    parts=[
                        Mock(inline_data=Mock(data=b"img", mime_type="image/png")),
                    ]
                )
            )
        ]
    )
    p = GoogleProvider(client_factory=lambda **_: fake_client, gcs=None)
    out = p.generate_image(
        provider_model="gemini-3-pro-image-preview",
        prompt="x",
        aspect_ratio="1:1",
        image_size="1k",
        client=fake_client,
    )
    _, kwargs = fake_client.models.generate_content.call_args
    assert kwargs["config"].image_config.output_mime_type is None
    assert out["mime_type"] == "image/png"
    assert out["bytes"] == b"img"
