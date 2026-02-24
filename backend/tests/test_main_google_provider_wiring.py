from __future__ import annotations

import types

import creativeai_studio.main as main_module
from creativeai_studio.config import AppConfig


def test_create_app_wires_google_provider_with_nano_banana_and_veo(monkeypatch, tmp_path):
    calls: dict[str, object] = {}

    class _NanoSpy:
        def __init__(self, *, client_factory):
            calls["nano_client_factory"] = client_factory
            calls["nano_instance"] = self

    class _VeoSpy:
        def __init__(self, *, client_factory):
            calls["veo_client_factory"] = client_factory
            calls["veo_instance"] = self

    class _GoogleSpy:
        def __init__(self, client_factory, *, nano_banana_provider=None, veo_provider=None):
            calls["google_client_factory"] = client_factory
            calls["google_nano_banana_provider"] = nano_banana_provider
            calls["google_veo_provider"] = veo_provider

        def make_client_api_key(self, api_key: str):  # pragma: no cover - not used in this test
            return {"api_key": api_key}

    fake_google = types.SimpleNamespace(genai=types.SimpleNamespace(Client=object))
    monkeypatch.setitem(__import__("sys").modules, "google", fake_google)
    monkeypatch.setattr(main_module, "NanoBananaProvider", _NanoSpy)
    monkeypatch.setattr(main_module, "VeoProvider", _VeoSpy)
    monkeypatch.setattr(main_module, "GoogleProvider", _GoogleSpy)

    app = main_module.create_app(AppConfig(data_dir=tmp_path / "data"))

    assert "google" in app.state.runner._providers
    assert calls["nano_client_factory"] is object
    assert calls["veo_client_factory"] is object
    assert calls["google_client_factory"] is object
    assert calls["google_nano_banana_provider"] is calls["nano_instance"]
    assert calls["google_veo_provider"] is calls["veo_instance"]
