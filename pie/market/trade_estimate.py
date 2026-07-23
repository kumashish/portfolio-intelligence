"""VIX-based estimated option trade plans without option-chain pricing."""

import calendar
import math
from datetime import date, timedelta
from enum import StrEnum

from pydantic import Field

from pie.core.models import DomainModel
from pie.market.strategy import StrategyRecommendation, StrategyType

TARGET_DAYS_TO_EXPIRY = 37
MINIMUM_DAYS_TO_EXPIRY = 30
MAXIMUM_DAYS_TO_EXPIRY = 45


class OptionRight(StrEnum):
    """The option right used by an estimated spread leg."""

    CALL = "call"
    PUT = "put"


class TradeLeg(DomainModel):
    """One estimated option leg without premium data."""

    action: str
    right: OptionRight
    strike: float = Field(gt=0.0)


class EstimatedTrade(DomainModel):
    """Estimated debit-spread plan derived from spot and annualized VIX."""

    strategy: StrategyType
    expiration: date
    spot_price: float = Field(gt=0.0)
    annualized_vix: float = Field(gt=0.0)
    expected_move: float = Field(gt=0.0)
    legs: tuple[TradeLeg, ...]
    exit_strategy: tuple[str, ...]
    disclaimer: str


def estimate_trade(
    symbol: str,
    spot_price: float,
    annualized_vix: float,
    recommendation: StrategyRecommendation,
    as_of: date | None = None,
) -> EstimatedTrade | None:
    """Estimate a debit spread from live spot/VIX inputs, without option pricing."""
    if recommendation.strategy not in {
        StrategyType.CALL_DEBIT_SPREAD,
        StrategyType.PUT_DEBIT_SPREAD,
    }:
        return None
    today = as_of or date.today()
    expiration = _select_expiration(today)
    days_to_expiry = (expiration - today).days
    expected_move = spot_price * (annualized_vix / 100.0) * math.sqrt(days_to_expiry / 365.0)
    increment = _strike_increment(symbol)
    long_strike = _round_to_increment(spot_price, increment)
    width = max(increment, _round_to_increment(expected_move * 0.75, increment))
    if recommendation.strategy is StrategyType.CALL_DEBIT_SPREAD:
        legs = (
            TradeLeg(action="buy", right=OptionRight.CALL, strike=long_strike),
            TradeLeg(action="sell", right=OptionRight.CALL, strike=long_strike + width),
        )
        exit_strategy = (
            "Exit if the trend regime becomes Neutral, Bear, or Strong Bear.",
            "Exit if spot closes below EMA50.",
            "Reassess or close at 21 days to expiry.",
        )
    else:
        legs = (
            TradeLeg(action="buy", right=OptionRight.PUT, strike=long_strike),
            TradeLeg(action="sell", right=OptionRight.PUT, strike=long_strike - width),
        )
        exit_strategy = (
            "Exit if the trend regime becomes Neutral, Bull, or Strong Bull.",
            "Exit if spot closes above EMA50.",
            "Reassess or close at 21 days to expiry.",
        )
    return EstimatedTrade(
        strategy=recommendation.strategy,
        expiration=expiration,
        spot_price=spot_price,
        annualized_vix=annualized_vix,
        expected_move=round(expected_move, 2),
        legs=legs,
        exit_strategy=exit_strategy,
        disclaimer=(
            "Estimated from spot and annualized VIX only; premiums, liquidity, "
            "and execution are not included."
        ),
    )


def _select_expiration(today: date) -> date:
    expirations = [_last_tuesday(today.year, month) for month in range(1, 13)]
    expirations.extend(_last_tuesday(today.year + 1, month) for month in range(1, 4))
    eligible = [
        expiration
        for expiration in expirations
        if MINIMUM_DAYS_TO_EXPIRY <= (expiration - today).days <= MAXIMUM_DAYS_TO_EXPIRY
    ]
    if eligible:
        return min(
            eligible, key=lambda expiration: abs((expiration - today).days - TARGET_DAYS_TO_EXPIRY)
        )
    target = today + timedelta(days=TARGET_DAYS_TO_EXPIRY)
    return target + timedelta(days=(1 - target.weekday()) % 7)


def _last_tuesday(year: int, month: int) -> date:
    last_day = calendar.monthrange(year, month)[1]
    candidate = date(year, month, last_day)
    return candidate - timedelta(days=(candidate.weekday() - 1) % 7)


def _strike_increment(symbol: str) -> float:
    return 50.0 if symbol == "^NSEI" else 1.0


def _round_to_increment(value: float, increment: float) -> float:
    return round(round(value / increment) * increment, 2)
