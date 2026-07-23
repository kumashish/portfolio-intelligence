"""JSON report persistence for individual market-analysis runs."""

import json
import re
from datetime import UTC, datetime
from pathlib import Path

from pie.core.models import MarketSnapshot
from pie.market.indicators.base import IndicatorResult
from pie.market.trend.models import TrendAnalysis


def write_market_report(
    output_dir: Path,
    snapshot: MarketSnapshot,
    indicators: dict[str, IndicatorResult],
    trend: TrendAnalysis,
) -> Path:
    """Write one timestamped market-analysis report and return its path."""
    generated_at = datetime.now(UTC)
    safe_symbol = re.sub(r"[^A-Za-z0-9_-]+", "_", snapshot.symbol).strip("_")
    report_path = output_dir / f"{safe_symbol}_{generated_at:%Y%m%dT%H%M%SZ}.json"
    payload = {
        "generated_at": generated_at.isoformat(),
        "snapshot": snapshot.model_dump(mode="json"),
        "indicators": {
            name: {
                "value": result.value,
                "warmup_complete": result.warmup_complete,
                "valid": result.valid,
                "reason": result.reason,
                "metadata": result.metadata,
            }
            for name, result in indicators.items()
        },
        "trend": trend.model_dump(mode="json"),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return report_path
