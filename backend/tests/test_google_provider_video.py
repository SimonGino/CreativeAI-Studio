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
