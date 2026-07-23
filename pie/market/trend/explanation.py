"""Human-readable rendering of deterministic trend-rule outcomes."""

from collections.abc import Collection

from pie.market.trend.models import TrendScore
from pie.market.trend.rules import RuleResult


def build_explanation(score: TrendScore, results: Collection[RuleResult]) -> str:
    """Build a concise explanation showing every passed and failed rule."""
    lines = [f"Trend Score: {score.value:.1f}", "", "Reason:"]
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        lines.append(f"[{status}] {result.explanation}")
    return "\n".join(lines)
