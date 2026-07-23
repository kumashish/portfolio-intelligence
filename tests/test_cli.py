import polars as pl
import pytest
from typer.testing import CliRunner

from pie.cli import app as cli_app
from pie.providers.yahoo import YahooFinanceProvider

runner = CliRunner()


def test_analyze_market_command_renders_indicators(monkeypatch: pytest.MonkeyPatch) -> None:
    data = pl.DataFrame(
        {
            "timestamp": list(range(201)),
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

    result = runner.invoke(cli_app.app, ["analyze-market", "SPY"])

    assert result.exit_code == 0
    assert "Market Snapshot: SPY" in result.output
    assert "EMA200" in result.output
