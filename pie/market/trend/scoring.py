"""Scoring and regime classification for trend-rule outcomes."""

from collections.abc import Collection, Mapping

from pie.market.indicators.base import IndicatorResult
from pie.market.trend.models import ConfidenceScore, MarketRegime, TrendScore
from pie.market.trend.rules import RuleResult


def calculate_trend_score(results: Collection[RuleResult]) -> TrendScore:
    """Normalize passed rule weights to the inclusive zero-to-ten range."""
    total_weight = sum(result.weight for result in results)
    if total_weight <= 0:
        return TrendScore(value=0.0)
    passed_weight = sum(result.weight for result in results if result.passed)
    return TrendScore(value=round((passed_weight / total_weight) * 10.0, 2))


def calculate_confidence(
    indicators: Mapping[str, IndicatorResult], results: Collection[RuleResult]
) -> ConfidenceScore:
    """Score analysis completeness from indicator validity, warmup, and evaluated rules."""
    if not indicators or not results:
        return ConfidenceScore(value=0.0)
    valid_indicators = sum(result.valid for result in indicators.values())
    warmed_indicators = sum(result.warmup_complete for result in indicators.values())
    evaluated_rules = sum(result.evaluated for result in results)
    indicator_completeness = valid_indicators / len(indicators)
    warmup_completeness = warmed_indicators / len(indicators)
    rule_completeness = evaluated_rules / len(results)
    return ConfidenceScore(
        value=round((indicator_completeness + warmup_completeness + rule_completeness) / 3.0, 2)
    )


def classify_regime(
    score: TrendScore, confidence: ConfidenceScore, results: Collection[RuleResult]
) -> MarketRegime:
    """Classify a trend score without making any trading decision."""
    if not any(result.evaluated for result in results) or confidence.value == 0.0:
        return MarketRegime.UNKNOWN
    if score.value >= 8.0:
        return MarketRegime.STRONG_BULL
    if score.value >= 6.0:
        return MarketRegime.BULL
    if score.value >= 4.0:
        return MarketRegime.NEUTRAL
    if score.value >= 2.0:
        return MarketRegime.BEAR
    return MarketRegime.STRONG_BEAR
