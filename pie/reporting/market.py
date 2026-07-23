"""Plain-text dashboard persistence for individual market-analysis runs."""

import re
from datetime import UTC, datetime
from pathlib import Path

from pie.core.models import MarketSnapshot
from pie.market.indicators.base import IndicatorResult
from pie.market.strategy import StrategyRecommendation
from pie.market.trend.models import TrendAnalysis


def write_market_report(
    output_dir: Path,
    snapshot: MarketSnapshot,
    indicators: dict[str, IndicatorResult],
    trend: TrendAnalysis,
    recommendation: StrategyRecommendation,
) -> Path:
    """Write one timestamped market dashboard and return its path."""
    generated_at = datetime.now(UTC)
    safe_symbol = re.sub(r"[^A-Za-z0-9_-]+", "_", snapshot.symbol).strip("_")
    report_path = output_dir / f"{safe_symbol}_{generated_at:%Y%m%dT%H%M%SZ}.txt"
    indicator_lines = [
        f"{name:<12}: {result.value:,.2f}"
        if result.valid and result.value is not None
        else f"{name:<12}: N/A"
        for name, result in indicators.items()
    ]
    limitation_lines = [f"- {limitation}" for limitation in recommendation.limitations]
    dashboard = "\n".join(
        [
            "PORTFOLIO INTELLIGENCE ENGINE",
            "=" * 32,
            "",
            f"Generated At : {generated_at:%Y-%m-%d %H:%M:%S UTC}",
            f"Symbol       : {snapshot.symbol}",
            f"Last Price   : {float(snapshot.last_price):,.2f}",
            "",
            "MARKET INTELLIGENCE",
            "-" * 19,
            f"Regime       : {trend.regime.replace('_', ' ').title()}",
            f"Trend Score  : {trend.trend_score.value:.1f} / 10",
            f"Confidence   : {trend.confidence.value:.0%}",
            "",
            "INDICATORS",
            "-" * 10,
            *indicator_lines,
            "",
            "RECOMMENDATION",
            "-" * 14,
            f"Strategy     : {recommendation.strategy.replace('_', ' ').title()}",
            f"Actionable   : {'Yes' if recommendation.actionable else 'No'}",
            f"Rationale    : {recommendation.rationale}",
            *limitation_lines,
            "",
            "TREND EXPLANATION",
            "-" * 17,
            trend.explanation,
            "",
        ]
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.write_text(dashboard, encoding="utf-8")
    return report_path
