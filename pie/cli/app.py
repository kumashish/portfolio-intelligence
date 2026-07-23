"""Typer command-line interface."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from pie.config.loader import load_config
from pie.config.models import TrendWeights
from pie.market.indicators.engine import IndicatorEngine
from pie.market.trend.engine import TrendEngine
from pie.market_data.exceptions import MarketDataError
from pie.market_data.snapshots import SnapshotBuilder
from pie.providers.yahoo import UrllibHTTPClient, YahooFinanceProvider

app = typer.Typer(help="Portfolio Intelligence Engine.", no_args_is_help=True)
console = Console()


@app.command("analyze-market")
def analyze_market(
    symbol: str,
    config: Annotated[
        Path | None, typer.Option(help="Optional YAML indicator configuration.")
    ] = None,
) -> None:
    """Fetch market data and calculate configured technical indicators."""
    try:
        data = YahooFinanceProvider(UrllibHTTPClient()).fetch_history(
            symbol,
            period="2y",
            interval="1d",
        )
    except MarketDataError as error:
        console.print(f"Unable to analyze {symbol}: {error}", style="red")
        raise typer.Exit(code=1) from error
    application_config = load_config(config) if config is not None else None
    configurations = application_config.indicators if application_config is not None else []
    engine = (
        IndicatorEngine.from_config(configurations) if configurations else IndicatorEngine.default()
    )
    results = engine.calculate(data)
    snapshots = SnapshotBuilder().build(symbol, data)
    snapshot = snapshots[-1]
    trend = TrendEngine.from_weights(
        application_config.trend.weights.as_mapping()
        if application_config is not None
        else TrendWeights().as_mapping()
    ).analyze(snapshot, results, data)
    table = Table(title=f"Market Snapshot: {symbol}")
    table.add_column("Indicator")
    table.add_column("Value", justify="right")
    table.add_row("Last Price", f"{float(snapshot.last_price):,.2f}")
    for result in results.values():
        value = f"{result.value:,.2f}" if result.valid and result.value is not None else "N/A"
        table.add_row(result.name, value)
    console.print(table)
    console.print(f"Market Regime: {trend.regime.replace('_', ' ').title()}")
    console.print(f"Trend Score: {trend.trend_score.value:.1f}")
    console.print(f"Confidence: {trend.confidence.value:.0%}")
    console.print(trend.explanation)


@app.command()
def portfolio(account_id: str) -> None:
    """Placeholder command for inspecting a portfolio."""
    console.print(f"Portfolio inspection for {account_id} is not implemented yet.")


@app.command()
def recommend(account_id: str) -> None:
    """Placeholder command for producing a recommendation."""
    console.print(f"Recommendation generation for {account_id} is not implemented yet.")


@app.command("config-check")
def config_check(path: Path) -> None:
    """Validate a configuration file."""
    load_config(path)
    console.print(f"Configuration is valid: {path}")


def main() -> None:
    """Run the CLI application."""
    app()
