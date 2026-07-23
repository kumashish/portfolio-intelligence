from pie.providers.registry import discover_providers


def test_discover_providers_returns_mapping() -> None:
    assert isinstance(discover_providers(), dict)
