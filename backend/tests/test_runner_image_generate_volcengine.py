from io import BytesIO

from PIL import Image

from creativeai_studio.config import AppConfig
from creativeai_studio.main import create_app
from creativeai_studio.runner import JobRunner


def _png_bytes(color: tuple[int, int, int]) -> bytes:
    buf = BytesIO()
    Image.new("RGB", (8, 8), color=color).save(buf, format="PNG")
    return buf.getvalue()


class _DummyArkProvider:
    def make_client_api_key(self, api_key: str):  # noqa: ARG002
        return object()

    def generate_image(self, **__):
        return {
            "items": [
                {"bytes": _png_bytes((255, 0, 0)), "mime_type": "image/png"},
                {"bytes": _png_bytes((0, 255, 0)), "mime_type": "image/png"},
                {"bytes": _png_bytes((0, 0, 255)), "mime_type": "image/png"},
            ]
        }


def test_runner_image_generate_volcengine_stores_multiple_outputs(tmp_path):
    app = create_app(AppConfig(data_dir=tmp_path / "data"))
    ctx = app.state.ctx
    ctx.settings.set_str("ark_api_key", "ark_x")

    ctx.jobs.create(
        job_id="j1",
        job_type="image.generate",
        model_id="doubao-seedream-4-5-251128",
        auth_mode="api_key",
        params={
            "prompt": "x",
            "aspect_ratio": "1:1",
            "image_size": "2k",
            "sequential_image_generation": "auto",
            "sequential_image_generation_options": {"max_images": 3},
        },
    )

    runner = JobRunner(ctx, providers={"volcengine_ark": _DummyArkProvider()}, concurrency=1)
    runner._run_one("j1")

    job = ctx.jobs.get("j1")
    assert job is not None
    assert job["status"] == "succeeded"
    outputs = job["result"]["outputs"]
    assert len(outputs) == 3
    assert [o["index"] for o in outputs] == [0, 1, 2]
    assert all(o["media_type"] == "image" for o in outputs)
    assert job["result"]["output_asset_id"] == outputs[0]["asset_id"]

    for out in outputs:
        asset = ctx.assets.get(out["asset_id"])
        assert asset is not None
        assert asset["media_type"] == "image"
