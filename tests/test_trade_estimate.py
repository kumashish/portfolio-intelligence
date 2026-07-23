from datetime import date

from pie.market.strategy import StrategyRecommendation, StrategyType
from pie.market.trade_estimate import OptionRight, estimate_trade


def recommendation(strategy: StrategyType) -> StrategyRecommendation:
    return StrategyRecommendation(
        strategy=strategy, actionable=True, rationale="Test recommendation"
    )


def test_call_debit_spread_uses_spot_vix_and_monthly_expiry() -> None:
    trade = estimate_trade(
        "^NSEI",
        24000.0,
        15.0,
        recommendation(StrategyType.CALL_DEBIT_SPREAD),
        as_of=date(2026, 7, 24),
    )

    assert trade is not None
    assert trade.expiration == date(2026, 8, 25)
    assert trade.legs[0].right is OptionRight.CALL
    assert trade.legs[0].strike == 24000.0
    assert trade.legs[1].strike > trade.legs[0].strike
    assert any("EMA50" in rule for rule in trade.exit_strategy)


def test_put_debit_spread_places_short_leg_below_long_leg() -> None:
    trade = estimate_trade(
        "^NSEI",
        24000.0,
        15.0,
        recommendation(StrategyType.PUT_DEBIT_SPREAD),
        as_of=date(2026, 7, 24),
    )

    assert trade is not None
    assert trade.legs[0].right is OptionRight.PUT
    assert trade.legs[1].strike < trade.legs[0].strike


def test_no_trade_strategy_does_not_create_estimate() -> None:
    trade = estimate_trade(
        "^NSEI",
        24000.0,
        15.0,
        recommendation(StrategyType.NO_TRADE),
        as_of=date(2026, 7, 24),
    )

    assert trade is None
