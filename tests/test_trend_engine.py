from datetime import datetime
from decimal import Decimal

import polars as pl

from pie.config.models import TrendWeights
from pie.core.models import MarketSnapshot
from pie.market.indicators.base import IndicatorResult
from pie.market.trend.engine import TrendEngine
from pie.market.trend.models import MarketRegime


def snapshot(price: float = 120.0) -> MarketSnapshot:
    return MarketSnapshot(
        symbol="SPY",
        observed_at=datetime(2026, 1, 1),
        last_price=Decimal(str(price)),
    )


def history(expanding: bool = True, structure: bool = True) -> pl.DataFrame:
    highs = [110.0 + index for index in range(16)]
    lows = [90.0 + index for index in range(16)]
    if not structure:
        highs[-1] = highs[-2]
        lows[-1] = lows[-2]
    if expanding:
        highs[-1] += 10.0
        lows[-1] -= 10.0
    return pl.DataFrame(
        {
            "high": highs,
            "low": lows,
            "close": [100.0 + index for index in range(16)],
        }
    )


def indicators(
    *,
    ema20: float = 115.0,
    ema50: float = 110.0,
    ema200: float = 100.0,
    rsi: float = 55.0,
    adx: float = 30.0,
    valid: bool = True,
    warmup_complete: bool = True,
) -> dict[str, IndicatorResult]:
    return {
        "EMA20": IndicatorResult("EMA20", ema20, warmup_complete, valid),
        "EMA50": IndicatorResult("EMA50", ema50, warmup_complete, valid),
        "EMA200": IndicatorResult("EMA200", ema200, warmup_complete, valid),
        "RSI(14)": IndicatorResult("RSI(14)", rsi, warmup_complete, valid),
        "ADX(14)": IndicatorResult("ADX(14)", adx, warmup_complete, valid),
    }


def analyze(
    indicator_values: dict[str, IndicatorResult],
    price_history: pl.DataFrame | None = None,
) -> MarketRegime:
    engine = TrendEngine.from_weights(TrendWeights().as_mapping())
    resolved_history = price_history if price_history is not None else history()
    return engine.analyze(snapshot(), indicator_values, resolved_history).regime


def test_strong_bull_trend() -> None:
    assert analyze(indicators()) is MarketRegime.STRONG_BULL


def test_bull_trend() -> None:
    assert (
        analyze(indicators(rsi=30.0, adx=20.0), history(expanding=False, structure=False))
        is MarketRegime.BULL
    )


def test_neutral_market() -> None:
    assert (
        analyze(indicators(ema20=80.0, ema50=90.0, ema200=100.0, adx=20.0), history(False, False))
        is MarketRegime.NEUTRAL
    )


def test_bear_trend() -> None:
    assert (
        analyze(
            indicators(ema20=100.0, ema50=140.0, ema200=130.0, rsi=30.0, adx=20.0),
            history(False, False),
        )
        is MarketRegime.BEAR
    )


def test_strong_bear_trend() -> None:
    assert (
        analyze(
            indicators(ema20=90.0, ema50=110.0, ema200=130.0, rsi=30.0, adx=20.0),
            history(False, False),
        )
        is MarketRegime.STRONG_BEAR
    )


def test_missing_indicators_reduce_confidence() -> None:
    engine = TrendEngine.from_weights(TrendWeights().as_mapping())

    analysis = engine.analyze(snapshot(), {}, history())

    assert analysis.confidence.value < 1.0
    assert "EMA200" in analysis.failed_rules[0]


def test_warmup_incomplete_reduces_confidence() -> None:
    engine = TrendEngine.from_weights(TrendWeights().as_mapping())

    analysis = engine.analyze(snapshot(), indicators(warmup_complete=False), history())

    assert analysis.confidence.value < 1.0
    assert analysis.trend_score.value < 10.0


def test_invalid_data_is_handled_deterministically() -> None:
    engine = TrendEngine.from_weights(TrendWeights().as_mapping())

    analysis = engine.analyze(snapshot(), indicators(valid=False), pl.DataFrame())

    assert analysis.regime is MarketRegime.UNKNOWN
    assert analysis.failed_rules


def test_configuration_controls_rule_weights() -> None:
    engine = TrendEngine.from_weights(
        {
            "ema200": 100.0,
            "ema_cross": 0.0,
            "ema_stack": 0.0,
            "adx": 0.0,
            "rsi": 0.0,
            "atr": 0.0,
            "structure": 0.0,
        }
    )

    analysis = engine.analyze(snapshot(), indicators(), history(False, False))

    assert analysis.trend_score.value == 10.0
