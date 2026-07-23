from datetime import datetime, timedelta

import polars as pl
import pytest

from pie.config.models import TrendWeights
from pie.market.backtest.engine import TrendBacktester
from pie.market.backtest.models import SignalDirection
from pie.market.indicators.engine import IndicatorEngine
from pie.market.trend.engine import TrendEngine
from pie.market.trend.models import MarketRegime


def market_data(rows: int = 200) -> pl.DataFrame:
    closes = [100.0 + index for index in range(rows)]
    return pl.DataFrame(
        {
            "timestamp": [datetime(2020, 1, 1) + timedelta(days=index) for index in range(rows)],
            "open": closes,
            "high": [close + 1.0 for close in closes],
            "low": [close - 1.0 for close in closes],
            "close": closes,
            "volume": [1_000] * rows,
        }
    )


def backtester() -> TrendBacktester:
    return TrendBacktester(
        IndicatorEngine.default(),
        TrendEngine.from_weights(TrendWeights().as_mapping()),
    )


def test_backtest_closes_a_signal_at_end_of_data() -> None:
    report = backtester().run("SPY", market_data())

    assert len(report.trades) == 1
    assert report.trades[0].direction is SignalDirection.LONG
    assert report.trades[0].exit_reason == "end_of_data"


def test_short_trade_return_is_positive_when_price_declines() -> None:
    trade = TrendBacktester._close_trade(
        SignalDirection.SHORT,
        datetime(2020, 1, 1),
        100.0,
        MarketRegime.BEAR,
        datetime(2020, 1, 2),
        90.0,
        "regime_reversal",
    )

    assert trade.return_percent == 10.0


def test_backtest_rejects_insufficient_history() -> None:
    with pytest.raises(ValueError, match="requires 200"):
        backtester().run("SPY", market_data(199))
