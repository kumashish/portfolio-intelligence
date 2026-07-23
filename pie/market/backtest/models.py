"""Immutable output models for signal-level backtests."""

from datetime import datetime
from enum import StrEnum

from pydantic import Field

from pie.core.models import DomainModel
from pie.market.trend.models import MarketRegime


class SignalDirection(StrEnum):
    """Directional exposure represented by a trend signal."""

    LONG = "long"
    SHORT = "short"


class BacktestTrade(DomainModel):
    """One closed historical directional trend signal."""

    direction: SignalDirection
    entry_at: datetime
    exit_at: datetime
    entry_price: float = Field(gt=0.0)
    exit_price: float = Field(gt=0.0)
    return_percent: float
    entry_regime: MarketRegime
    exit_reason: str


class BacktestReport(DomainModel):
    """Aggregate performance of historical directional signals."""

    symbol: str
    trades: tuple[BacktestTrade, ...]
    win_rate: float = Field(ge=0.0, le=1.0)
    average_return_percent: float
    cumulative_return_percent: float
    maximum_drawdown_percent: float = Field(le=0.0)
    assumptions: tuple[str, ...]
