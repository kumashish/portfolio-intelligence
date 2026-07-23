"""Pydantic configuration models."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ConfigModel(BaseModel):
    """Base model for configuration values."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class LoggingConfig(ConfigModel):
    """Logging settings."""

    level: str = "INFO"
    render_json: bool = False


class ProviderConfig(ConfigModel):
    """Configuration for a provider plugin."""

    enabled: bool = True
    options: dict[str, Any] = Field(default_factory=dict)


class AppConfig(ConfigModel):
    """Top-level application configuration."""

    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
