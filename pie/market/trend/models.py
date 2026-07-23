"""Immutable domain models for quantitative trend analysis."""

from datetime import datetime
from enum import StrEnum

from pydantic import Field

from pie.core.models import DomainModel


class MarketRegime(StrEnum):
    """Discrete classification of a quantitative trend score."""

    UNKNOWN = "unknown"
    STRONG_BULL = "strong_bull"
    BULL = "bull"
    NEUTRAL = "neutral"
    BEAR = "bear"
    STRONG_BEAR = "strong_bear"


class TrendScore(DomainModel):
    """A normalized trend score ranging from zero to ten."""

    value: float = Field(ge=0.0, le=10.0)


class ConfidenceScore(DomainModel):
    """Confidence in the completeness of a trend analysis."""

    value: float = Field(ge=0.0, le=1.0)


class TrendAnalysis(DomainModel):
    """Deterministic market-trend assessment without trade recommendations."""

    symbol: str = Field(min_length=1)
    timestamp: datetime
    trend_score: TrendScore
    confidence: ConfidenceScore
    regime: MarketRegime
    explanation: str = Field(min_length=1)
    indicator_values: dict[str, float | None]
    passed_rules: tuple[str, ...] = ()
    failed_rules: tuple[str, ...] = ()
