"""Validation rules for canonical OHLCV data."""

from dataclasses import dataclass

import polars as pl
import structlog

from pie.market_data.exceptions import ValidationError

REQUIRED_COLUMNS = frozenset({"timestamp", "open", "high", "low", "close", "volume"})

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class MarketDataValidator:
    """Validate historical OHLCV data before it enters the domain."""

    minimum_history: int = 30

    def validate(self, data: pl.DataFrame) -> None:
        """Raise a domain error when a DataFrame violates market-data invariants."""
        log = logger.bind(rows=data.height, columns=data.columns)
        missing_columns = REQUIRED_COLUMNS.difference(data.columns)
        if missing_columns:
            log.warning("market_data_validation_failed", reason="missing_columns")
            msg = f"Market data is missing required columns: {sorted(missing_columns)}"
            raise ValidationError(msg)
        if data.height < self.minimum_history:
            log.warning("market_data_validation_failed", reason="insufficient_history")
            msg = f"Market data requires at least {self.minimum_history} rows."
            raise ValidationError(msg)
        if data.select(pl.col("timestamp").is_duplicated().any()).item():
            log.warning("market_data_validation_failed", reason="duplicate_timestamps")
            msg = "Market data contains duplicate timestamps."
            raise ValidationError(msg)
        for column in REQUIRED_COLUMNS:
            if data.get_column(column).null_count() > 0:
                log.warning("market_data_validation_failed", reason="null_values", column=column)
                msg = f"Market data contains null values in '{column}'."
                raise ValidationError(msg)
        if data.filter(pl.col("volume") < 0).height > 0:
            log.warning("market_data_validation_failed", reason="negative_volume")
            msg = "Market data contains negative volume."
            raise ValidationError(msg)
        log.info("market_data_validated")
