from unittest.mock import Mock

import pytest

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
    p = GoogleProvider(client_factory=lambda **_: fake_client)
    out = p.generate_image(
        provider_model="gemini-3-pro-image-preview",
        prompt="x",
        aspect_ratio="1:1",
        image_size="1k",
        client=fake_client,
    )
    _, kwargs = fake_client.models.generate_content.call_args
    assert kwargs["config"].image_config.output_mime_type is None
    assert kwargs["config"].image_config.image_size == "1K"
    assert out["mime_type"] == "image/png"
    assert out["bytes"] == b"img"


def test_generate_image_with_gemini_flash_omits_image_size():
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
    p = GoogleProvider(client_factory=lambda **_: fake_client)
    out = p.generate_image(
        provider_model="gemini-2.5-flash-image",
        prompt="x",
        aspect_ratio="16:9",
        image_size="2k",
        client=fake_client,
    )
    _, kwargs = fake_client.models.generate_content.call_args
    assert kwargs["config"].image_config.aspect_ratio == "16:9"
    assert kwargs["config"].image_config.image_size is None
    assert out["mime_type"] == "image/png"
    assert out["bytes"] == b"img"


def test_generate_image_with_gemini_reads_response_parts_shape():
    fake_client = Mock()
    fake_client.models.generate_content.return_value = Mock(
        parts=[Mock(inline_data=Mock(data=b"img", mime_type="image/png"))],
        candidates=None,
    )
    p = GoogleProvider(client_factory=lambda **_: fake_client)
    out = p.generate_image(
        provider_model="gemini-2.5-flash-image",
        prompt="x",
        aspect_ratio="1:1",
        image_size="1k",
        client=fake_client,
    )
    assert out["mime_type"] == "image/png"
    assert out["bytes"] == b"img"


def test_generate_image_with_gemini_no_image_includes_diagnostics():
    fake_client = Mock()
    fake_client.models.generate_content.return_value = Mock(
        parts=[Mock(text="Cannot generate this request.", inline_data=None)],
        candidates=[
            Mock(
                content=Mock(parts=[Mock(text="Cannot generate this request.", inline_data=None)]),
                finish_reason="SAFETY",
                finish_message="Blocked by policy",
            )
        ],
        prompt_feedback=Mock(block_reason_message="Policy blocked this prompt"),
    )
    p = GoogleProvider(client_factory=lambda **_: fake_client)
    with pytest.raises(RuntimeError, match="No image output") as exc_info:
        p.generate_image(
            provider_model="gemini-2.5-flash-image",
            prompt="x",
            aspect_ratio="1:1",
            image_size="1k",
            client=fake_client,
        )
    msg = str(exc_info.value)
    assert "Policy blocked this prompt" in msg
    assert "SAFETY" in msg
    assert "Blocked by policy" in msg
    assert "Cannot generate this request." in msg
