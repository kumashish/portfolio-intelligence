"""Immutable domain models for portfolio intelligence."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class DomainModel(BaseModel):
    """Base type for immutable domain values."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class OptionRight(StrEnum):
    """The right granted by an option contract."""

    CALL = "call"
    PUT = "put"


class PositionSide(StrEnum):
    """Directional side of a position."""

    LONG = "long"
    SHORT = "short"


class TradeAction(StrEnum):
    """Supported trade actions."""

    BUY = "buy"
    SELL = "sell"


class RecommendationAction(StrEnum):
    """Actions a recommendation can propose."""

    OPEN = "open"
    CLOSE = "close"
    HOLD = "hold"
    ADJUST = "adjust"


class Greeks(DomainModel):
    """Option sensitivity measures."""

    delta: Decimal
    gamma: Decimal
    theta: Decimal
    vega: Decimal
    rho: Decimal


class Position(DomainModel):
    """A single equity or option position."""

    symbol: str = Field(min_length=1)
    quantity: Decimal
    average_cost: Decimal
    market_value: Decimal
    side: PositionSide
    option_right: OptionRight | None = None
    strike: Decimal | None = None
    expiration: datetime | None = None
    greeks: Greeks | None = None


class Trade(DomainModel):
    """A proposed or executed trade."""

    symbol: str = Field(min_length=1)
    action: TradeAction
    quantity: Decimal
    price: Decimal | None = None
    option_right: OptionRight | None = None
    strike: Decimal | None = None
    expiration: datetime | None = None
    submitted_at: datetime | None = None


class MarketSnapshot(DomainModel):
    """Observed market data for one instrument at a point in time."""

    symbol: str = Field(min_length=1)
    observed_at: datetime
    last_price: Decimal
    bid: Decimal | None = None
    ask: Decimal | None = None
    implied_volatility: Decimal | None = None
    volume: int | None = Field(default=None, ge=0)


class PortfolioSnapshot(DomainModel):
    """Portfolio state captured at a point in time."""

    account_id: str = Field(min_length=1)
    observed_at: datetime
    net_liquidation_value: Decimal
    cash_balance: Decimal
    positions: tuple[Position, ...] = ()


class TrendAnalysis(DomainModel):
    """Descriptive trend assessment for an instrument."""

    symbol: str = Field(min_length=1)
    analyzed_at: datetime
    trend: str = Field(min_length=1)
    confidence: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    summary: str = Field(min_length=1)


class Recommendation(DomainModel):
    """An immutable recommendation derived from available analysis."""

    recommendation_id: str = Field(min_length=1)
    created_at: datetime
    action: RecommendationAction
    summary: str = Field(min_length=1)
    trade: Trade | None = None
    confidence: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
