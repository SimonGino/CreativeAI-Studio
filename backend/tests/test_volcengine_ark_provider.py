from types import SimpleNamespace

from creativeai_studio.providers.volcengine_ark_provider import VolcengineArkProvider


class _FakeImagesApi:
    def __init__(self):
        self.last_kwargs = None

    def generate(self, **kwargs):
        self.last_kwargs = kwargs
        return SimpleNamespace(data=[SimpleNamespace(url="https://example.com/a.png")])


class _FakeClient:
    def __init__(self):
        self.images = _FakeImagesApi()


def test_generate_image_builds_ark_payload_for_multi_reference_and_sequence():
    fake_client = _FakeClient()
    provider = VolcengineArkProvider(client_factory=lambda **_: fake_client)
    out = provider.generate_image(
        provider_model="doubao-seedream-4-5-251128",
        prompt="p",
        aspect_ratio="1:1",
        image_size="2k",
        reference_images=[
            {"bytes": b"a", "mime_type": "image/png"},
            {"bytes": b"b", "mime_type": "image/jpeg"},
        ],
        sequential_image_generation="auto",
        sequential_image_generation_options={"max_images": 4},
        watermark=True,
        client=fake_client,
    )

    assert out == {"items": [{"url": "https://example.com/a.png"}]}
    assert fake_client.images.last_kwargs is not None
    assert fake_client.images.last_kwargs["model"] == "doubao-seedream-4-5-251128"
    assert fake_client.images.last_kwargs["size"] == "2K"
    assert fake_client.images.last_kwargs["response_format"] == "url"

    extra = fake_client.images.last_kwargs["extra_body"]
    assert extra["sequential_image_generation"] == "auto"
    assert extra["sequential_image_generation_options"] == {"max_images": 4}
    assert extra["watermark"] is True
    assert isinstance(extra["image"], list)
    assert len(extra["image"]) == 2
    assert extra["image"][0].startswith("data:image/png;base64,")
    assert extra["image"][1].startswith("data:image/jpeg;base64,")


def test_make_client_api_key_passes_base_url_and_key():
    calls: list[dict] = []

    def _factory(**kwargs):
        calls.append(kwargs)
        return object()

    provider = VolcengineArkProvider(client_factory=_factory)
    provider.make_client_api_key("ark_x")
    assert calls == [{"base_url": "https://ark.cn-beijing.volces.com/api/v3", "api_key": "ark_x"}]
