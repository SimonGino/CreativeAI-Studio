from unittest.mock import Mock

from creativeai_studio.providers.google_provider import GoogleProvider


def test_generate_video_polls_and_returns_uri():
    fake_client = Mock()
    op0 = Mock(done=False)
    fake_client.models.generate_videos.return_value = op0

    op1 = Mock(done=True)
    op1.result = Mock(generated_videos=[Mock(video=Mock(uri="gs://b/out.mp4", mime_type="video/mp4"))])
    fake_client.operations.get.return_value = op1

    p = GoogleProvider(client_factory=lambda **_: fake_client)
    out = p.generate_video(
        provider_model="veo-3.1",
        prompt="x",
        duration_seconds=5,
        aspect_ratio="16:9",
        client=fake_client,
        poll_interval_seconds=0,
    )
    assert out["gcs_uri"] == "gs://b/out.mp4"


def test_generate_video_downloads_video_bytes_via_sdk_when_uri_is_returned():
    fake_client = Mock()
    op0 = Mock(done=False)
    fake_client.models.generate_videos.return_value = op0

    video = Mock(uri="https://example.invalid/video", mime_type="video/mp4")
    video.video_bytes = None
    op1 = Mock(done=True)
    op1.result = Mock(generated_videos=[Mock(video=video)])
    fake_client.operations.get.return_value = op1
    fake_client.files.download.return_value = b"mp4-bytes"

    p = GoogleProvider(client_factory=lambda **_: fake_client)
    out = p.generate_video(
        provider_model="veo-3.1-fast-generate-preview",
        prompt="x",
        duration_seconds=4,
        aspect_ratio="16:9",
        client=fake_client,
        poll_interval_seconds=0,
    )

    fake_client.files.download.assert_called_once_with(file=video)
    assert out["bytes"] == b"mp4-bytes"
    assert out["mime_type"] == "video/mp4"
