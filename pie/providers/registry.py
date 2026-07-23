"""Plugin discovery for provider implementations."""

from importlib.metadata import entry_points

from pie.providers.interfaces import Provider

PROVIDER_ENTRY_POINT_GROUP = "pie.providers"


def discover_providers() -> dict[str, type[Provider]]:
    """Discover provider classes registered through package entry points."""
    discovered: dict[str, type[Provider]] = {}
    for entry_point in entry_points(group=PROVIDER_ENTRY_POINT_GROUP):
        provider_type = entry_point.load()
        if not isinstance(provider_type, type) or not issubclass(provider_type, Provider):
            msg = f"Provider entry point '{entry_point.name}' must resolve to a Provider subclass."
            raise TypeError(msg)
        discovered[entry_point.name] = provider_type
    return discovered
