from datetime import datetime, timedelta

import polars as pl
import pytest

from pie.core.models import MarketSnapshot
from pie.market_data.exceptions import SnapshotError, ValidationError
from pie.market_data.snapshots import SnapshotBuilder
from pie.market_data.validation import MarketDataValidator


def market_data(rows: int = 3) -> pl.DataFrame:
    timestamps = [datetime(2026, 1, 1) + timedelta(days=index) for index in range(rows)]
    return pl.DataFrame(
        {
            "timestamp": timestamps,
            "open": [100.0 + index for index in range(rows)],
            "high": [101.0 + index for index in range(rows)],
            "low": [99.0 + index for index in range(rows)],
            "close": [100.5 + index for index in range(rows)],
            "volume": [1000 + index for index in range(rows)],
        }
    )


def test_validator_accepts_complete_history() -> None:
    MarketDataValidator(minimum_history=3).validate(market_data())


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (market_data().drop("close"), "missing required columns"),
        (market_data().with_columns(pl.lit(None).alias("close")), "null values"),
        (market_data().with_columns(pl.lit(-1).alias("volume")), "negative volume"),
        (
            market_data().with_columns(pl.col("timestamp").first().alias("timestamp")),
            "duplicate timestamps",
        ),
    ],
)
def test_validator_rejects_invalid_data(data: pl.DataFrame, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        MarketDataValidator(minimum_history=3).validate(data)


def test_validator_rejects_insufficient_history() -> None:
    with pytest.raises(ValidationError, match="at least 4 rows"):
        MarketDataValidator(minimum_history=4).validate(market_data())


def test_snapshot_builder_creates_immutable_domain_snapshots() -> None:
    snapshots = SnapshotBuilder(MarketDataValidator(minimum_history=3)).build("SPY", market_data())

    assert len(snapshots) == 3
    assert all(isinstance(snapshot, MarketSnapshot) for snapshot in snapshots)
    assert snapshots[-1].last_price == 102.5


def test_snapshot_builder_wraps_conversion_failures() -> None:
    invalid_data = market_data().with_columns(
        pl.Series("timestamp", ["not-a-date-1", "not-a-date-2", "not-a-date-3"])
    )

    with pytest.raises(SnapshotError):
        SnapshotBuilder(MarketDataValidator(minimum_history=3)).build("SPY", invalid_data)
