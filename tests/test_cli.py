from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import polars as pl
import pytest
from typer.testing import CliRunner

from pie.cli import app as cli_app
from pie.market.strategy import StrategyRecommendation, StrategyType
from pie.providers.yahoo import YahooFinanceProvider

runner = CliRunner()


def test_analyze_market_command_renders_indicators(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    data = pl.DataFrame(
        {
            "timestamp": [datetime(2026, 1, 1) + timedelta(days=index) for index in range(201)],
            "open": [100.0] * 201,
            "high": [101.0] * 201,
            "low": [99.0] * 201,
            "close": [100.0] * 201,
            "volume": [1_000] * 201,
        }
    )
    monkeypatch.setattr(
        YahooFinanceProvider,
        "fetch_history",
        lambda _self, _symbol, *, period, interval: data,
    )

    result = runner.invoke(cli_app.app, ["analyze-market", "SPY", "--output-dir", str(tmp_path)])

    assert result.exit_code == 0
    assert "Market Snapshot: SPY" in result.output
    assert "EMA200" in result.output
    assert len(list(tmp_path.glob("SPY_*.txt"))) == 1


def test_estimate_trade_uses_fallback_vix_when_provider_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable(*_args: object, **_kwargs: object) -> None:
        raise ValueError("VIX unavailable")

    monkeypatch.setattr(YahooFinanceProvider, "fetch_history", unavailable)

    trade = cli_app._estimate_trade(
        "SPY",
        Decimal("700"),
        StrategyRecommendation(
            strategy=StrategyType.CALL_DEBIT_SPREAD,
            actionable=True,
            rationale="Test recommendation",
        ),
    )

    assert trade is not None
    assert trade.vix_source == "fallback assumption"
