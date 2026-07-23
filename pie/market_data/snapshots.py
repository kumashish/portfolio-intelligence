"""Conversion from validated OHLCV data to immutable domain snapshots."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import polars as pl
import structlog
from pydantic import ValidationError as PydanticValidationError

from pie.core.models import MarketSnapshot
from pie.market_data.exceptions import SnapshotError
from pie.market_data.validation import MarketDataValidator

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class SnapshotBuilder:
    """Build immutable snapshots from validated canonical market data."""

    validator: MarketDataValidator = field(default_factory=MarketDataValidator)

    def build(self, symbol: str, data: pl.DataFrame) -> tuple[MarketSnapshot, ...]:
        """Convert each validated market-data row into a MarketSnapshot."""
        self.validator.validate(data)
        try:
            snapshot_data = data.sort("timestamp").select("timestamp", "close", "volume")
            rows = snapshot_data.iter_rows(named=True)
            snapshots = tuple(self._build_snapshot(symbol, row) for row in rows)
        except (InvalidOperation, PydanticValidationError, TypeError, ValueError) as error:
            logger.exception("market_snapshot_build_failed", symbol=symbol)
            msg = f"Unable to build market snapshots for '{symbol}'."
            raise SnapshotError(msg) from error
        logger.info("market_snapshots_built", symbol=symbol, count=len(snapshots))
        return snapshots

    @staticmethod
    def _build_snapshot(symbol: str, row: dict[str, Any]) -> MarketSnapshot:
        observed_at = row["timestamp"]
        if not isinstance(observed_at, datetime):
            msg = "Market data timestamp must be a datetime value."
            raise TypeError(msg)
        return MarketSnapshot(
            symbol=symbol,
            observed_at=observed_at,
            last_price=Decimal(str(row["close"])),
            volume=int(row["volume"]),
        )
