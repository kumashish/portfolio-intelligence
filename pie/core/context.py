"""Application context and provider access."""

from dataclasses import dataclass, field

import structlog

from pie.config.models import AppConfig
from pie.providers.interfaces import Provider


@dataclass(frozen=True, slots=True)
class Context:
    """Dependencies shared by application entry points."""

    config: AppConfig
    providers: dict[str, Provider] = field(default_factory=dict)
    logger: structlog.stdlib.BoundLogger = field(default_factory=structlog.get_logger)

    def provider(self, name: str) -> Provider:
        """Return a named provider dependency."""
        return self.providers[name]
