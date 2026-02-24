def test_providers_package_exports_expected_provider_classes():
    from creativeai_studio.providers import (  # noqa: PLC0415
        GoogleProvider,
        NanoBananaProvider,
        VeoProvider,
        VolcengineArkProvider,
    )

    assert GoogleProvider is not None
    assert NanoBananaProvider is not None
    assert VeoProvider is not None
    assert VolcengineArkProvider is not None
