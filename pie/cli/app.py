"""Typer command-line interface."""

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from pie.cli.readme import readme_app
from pie.config.loader import load_config
from pie.config.models import TrendWeights
from pie.core.signal_state import SignalStateManager
from pie.market.backtest.engine import TrendBacktester
from pie.market.indicators.engine import IndicatorEngine
from pie.market.strategy import StrategyRecommendation, select_strategy
from pie.market.trade_estimate import EstimatedTrade, estimate_trade
from pie.market.trend.engine import TrendEngine
from pie.market_data.csv_loader import load_ohlcv_csv
from pie.market_data.exceptions import MarketDataError
from pie.market_data.snapshots import SnapshotBuilder
from pie.providers.yahoo import UrllibHTTPClient, YahooFinanceProvider
from pie.reporting.market import write_market_report
from pie.reporting.snapshot import upsert_snapshot_entry

app = typer.Typer(help="Portfolio Intelligence Engine.", no_args_is_help=True)
app.add_typer(readme_app, name="readme")
console = Console()

MARKET_NAMES = {"^NSEI": "NIFTY 50", "^NSEBANK": "BANKNIFTY", "SPY": "SPY", "QQQ": "QQQ"}
OPTION_SYMBOL_NAMES = {"^NSEI": "NIFTY", "^NSEBANK": "BANKNIFTY", "SPY": "SPY", "QQQ": "QQQ"}
REGIME_LABELS = {
    "strong_bull": "🟢 Strong Bull",
    "bull": "🟢 Bull",
    "neutral": "🟡 Neutral",
    "bear": "🔴 Bear",
    "strong_bear": "🔴 Strong Bear",
    "unknown": "⚪ Unknown",
}

VIX_SYMBOLS = {"^NSEI": "^INDIAVIX", "SPY": "^VIX", "QQQ": "^VIX"}
FALLBACK_VIX = {"^NSEI": 15.0, "SPY": 20.0, "QQQ": 20.0}


def _format_strike(strike: float) -> str:
    return str(int(strike)) if strike == int(strike) else str(strike)


def format_trade_legs(symbol: str, estimated_trade: EstimatedTrade | None) -> str:
    """Render an estimated trade as option-symbol-style leg lines.

    e.g. "Buy NIFTY 28-Jul-2026-23600-PE<br>Sell NIFTY 28-Jul-2026-23000-PE"
    (<br> forces a line break inside a markdown table cell.)
    """
    if estimated_trade is None:
        return "No Trade"
    display_symbol = OPTION_SYMBOL_NAMES.get(symbol, symbol)
    expiry = estimated_trade.expiration.strftime("%d-%b-%Y")
    right_suffix = {"put": "PE", "call": "CE"}
    lines = [
        f"{leg.action.title()} {display_symbol} {expiry}-{_format_strike(leg.strike)}-"
        f"{right_suffix[leg.right.value]}"
        for leg in estimated_trade.legs
    ]
    return "<br>".join(lines)


@app.command("analyze-market")
def analyze_market(
    symbol: str,
    config: Annotated[
        Path | None, typer.Option(help="Optional YAML indicator configuration.")
    ] = None,
    output_dir: Annotated[
        Path, typer.Option(help="Directory for the timestamped text analysis report.")
    ] = Path("reports/market"),
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
    recommendation = select_strategy(trend)
    estimated_trade = _estimate_trade(symbol, snapshot.last_price, recommendation)
    report_path = write_market_report(
        output_dir,
        snapshot,
        results,
        trend,
        recommendation,
        estimated_trade,
    )
    generated_at = datetime.now(UTC)
    state, status = SignalStateManager().update_state(
        symbol=symbol,
        strategy=recommendation.strategy.value,
        regime=trend.regime.value,
    )
    if not recommendation.actionable:
        signal_label = "Hold"
    elif status in {"NEW", "CHANGED"}:
        signal_label = "NEW"
    else:
        signal_label = "Active"
    upsert_snapshot_entry(
        Path("reports/market/snapshot.json"),
        {
            "symbol": symbol,
            "market": MARKET_NAMES.get(symbol, symbol),
            "last_updated": generated_at.isoformat(),
            "trend": REGIME_LABELS.get(trend.regime.value, trend.regime.value),
            "strategy": format_trade_legs(symbol, estimated_trade),
            "signal": signal_label,
            "signal_since": state.trend_started_at.isoformat(),
        },
    )
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
    console.print(f"Recommendation: {recommendation.strategy.replace('_', ' ').title()}")
    if estimated_trade is not None:
        console.print(f"Suggested expiry: {estimated_trade.expiration.isoformat()}")
    console.print(f"Report saved: {report_path}")


@app.command("backtest-market")
def backtest_market(
    symbol: str,
    config: Annotated[
        Path | None, typer.Option(help="Optional YAML indicator and trend configuration.")
    ] = None,
    data_path: Annotated[
        Path | None, typer.Option(help="Optional local Date/Open/High/Low/Close/Volume CSV file.")
    ] = None,
) -> None:
    """Backtest directional trend signals against historical index returns."""
    if data_path is not None:
        data = load_ohlcv_csv(data_path)
    else:
        try:
            data = YahooFinanceProvider(UrllibHTTPClient()).fetch_history(
                symbol,
                period="5y",
                interval="1d",
            )
        except MarketDataError as error:
            console.print(f"Unable to backtest {symbol}: {error}", style="red")
            raise typer.Exit(code=1) from error
    application_config = load_config(config) if config is not None else None
    configurations = application_config.indicators if application_config is not None else []
    indicator_engine = (
        IndicatorEngine.from_config(configurations) if configurations else IndicatorEngine.default()
    )
    weights = (
        application_config.trend.weights.as_mapping()
        if application_config is not None
        else TrendWeights().as_mapping()
    )
    report = TrendBacktester(indicator_engine, TrendEngine.from_weights(weights)).run(symbol, data)
    table = Table(title=f"Trend Signal Backtest: {symbol}")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row("Closed signals", str(len(report.trades)))
    table.add_row("Win rate", f"{report.win_rate:.1%}")
    table.add_row("Average move", f"{report.average_return_percent:.2f}%")
    table.add_row("Cumulative return", f"{report.cumulative_return_percent:.2f}%")
    table.add_row("Maximum drawdown", f"{report.maximum_drawdown_percent:.2f}%")
    console.print(table)
    for assumption in report.assumptions:
        console.print(f"- {assumption}")


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


def _estimate_trade(
    symbol: str, spot_price: Decimal, recommendation: StrategyRecommendation
) -> EstimatedTrade | None:
    if not recommendation.actionable:
        return None
    vix_symbol = VIX_SYMBOLS.get(symbol, "^VIX")
    try:
        vix_data = YahooFinanceProvider(UrllibHTTPClient()).fetch_history(
            vix_symbol,
            period="5d",
            interval="1d",
        )
        vix = float(vix_data.get_column("close").tail(1).item())
        vix_source = f"live {vix_symbol}"
    except (IndexError, MarketDataError, TypeError, ValueError):
        vix = FALLBACK_VIX.get(symbol, 20.0)
        vix_source = "fallback assumption"
    return estimate_trade(symbol, float(spot_price), vix, recommendation, vix_source)
