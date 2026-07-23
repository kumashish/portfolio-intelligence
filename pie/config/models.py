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


class TrendWeights(ConfigModel):
    """YAML-configurable weights for quantitative trend rules."""

    ema200: float = Field(default=30.0, ge=0.0)
    ema_cross: float = Field(default=20.0, ge=0.0)
    ema_stack: float = Field(default=20.0, ge=0.0)
    adx: float = Field(default=10.0, ge=0.0)
    rsi: float = Field(default=10.0, ge=0.0)
    atr: float = Field(default=5.0, ge=0.0)
    structure: float = Field(default=5.0, ge=0.0)

    def as_mapping(self) -> dict[str, float]:
        """Return the weights in the form consumed by the trend engine."""
        return {
            "ema200": self.ema200,
            "ema_cross": self.ema_cross,
            "ema_stack": self.ema_stack,
            "adx": self.adx,
            "rsi": self.rsi,
            "atr": self.atr,
            "structure": self.structure,
        }


class TrendConfig(ConfigModel):
    """Configuration consumed only by the market trend engine."""

    weights: TrendWeights = Field(default_factory=TrendWeights)


class AppConfig(ConfigModel):
    """Top-level application configuration."""

    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    indicators: list[dict[str, dict[str, Any]]] = Field(default_factory=list)
    trend: TrendConfig = Field(default_factory=TrendConfig)
