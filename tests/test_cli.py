from typer.testing import CliRunner

from pie.cli.app import app

runner = CliRunner()


def test_analyze_market_command_is_available() -> None:
    result = runner.invoke(app, ["analyze-market", "SPY"])

    assert result.exit_code == 0
    assert "Market analysis for SPY" in result.output
