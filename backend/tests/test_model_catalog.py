from creativeai_studio.model_catalog import get_model


def test_nano_banana_has_expected_provider_models():
    m = get_model("nano-banana-pro")
    assert m is not None
    assert m["provider_id"] == "google"
    assert m["provider_models"]["image_generate"] == "gemini-3-pro-image-preview"
    assert "image_edit" not in (m.get("provider_models") or {})

    fast = get_model("nano-banana")
    assert fast is not None
    assert fast["provider_models"]["image_generate"] == "gemini-2.5-flash-image"
    assert fast["resolution_presets"] == ["1k"]
