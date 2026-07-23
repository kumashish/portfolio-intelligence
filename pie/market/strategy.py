"""Conservative advisory strategy selection from quantitative trend analysis."""

from enum import StrEnum

from pydantic import Field

from pie.core.models import DomainModel
from pie.market.trend.models import MarketRegime, TrendAnalysis

MINIMUM_CONFIDENCE = 0.75


class StrategyType(StrEnum):
    """Strategy types supported by the market-analysis dashboard."""

    NO_TRADE = "no_trade"
    CALL_DEBIT_SPREAD = "call_debit_spread"
    PUT_DEBIT_SPREAD = "put_debit_spread"
    BUTTERFLY = "butterfly"
    BROKEN_WING_BUTTERFLY = "broken_wing_butterfly"
    CREDIT_SPREAD = "credit_spread"


class StrategyRecommendation(DomainModel):
    """Advisory strategy outcome derived from trend conditions only."""

    strategy: StrategyType
    actionable: bool
    rationale: str = Field(min_length=1)
    limitations: tuple[str, ...] = ()


def select_strategy(analysis: TrendAnalysis) -> StrategyRecommendation:
    """Select only directional debit spreads; otherwise return a safe no-trade outcome."""
    if analysis.confidence.value < MINIMUM_CONFIDENCE:
        return StrategyRecommendation(
            strategy=StrategyType.NO_TRADE,
            actionable=False,
            rationale="Confidence is below the minimum threshold for an advisory trade.",
        )
    if analysis.regime in {MarketRegime.STRONG_BULL, MarketRegime.BULL}:
        return StrategyRecommendation(
            strategy=StrategyType.CALL_DEBIT_SPREAD,
            actionable=True,
            rationale="Confirmed bullish trend supports a directional call debit spread.",
            limitations=(
                "Validate estimated strikes and expiry against live option-chain liquidity "
                "and pricing.",
                "This is an advisory signal, not an execution instruction.",
            ),
        )
    if analysis.regime in {MarketRegime.STRONG_BEAR, MarketRegime.BEAR}:
        return StrategyRecommendation(
            strategy=StrategyType.PUT_DEBIT_SPREAD,
            actionable=True,
            rationale="Confirmed bearish trend supports a directional put debit spread.",
            limitations=(
                "Validate estimated strikes and expiry against live option-chain liquidity "
                "and pricing.",
                "This is an advisory signal, not an execution instruction.",
            ),
        )
    return StrategyRecommendation(
        strategy=StrategyType.NO_TRADE,
        actionable=False,
        rationale="Neutral or unknown market regime does not justify a directional trade.",
    )
