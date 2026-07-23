"""Shared contracts and safeguards for technical indicators."""

from dataclasses import dataclass, field
from time import perf_counter
from typing import Protocol

import polars as pl
import structlog

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class IndicatorResult:
    """The latest computed value and diagnostic state for an indicator."""

    name: str
    value: float | None
    warmup_complete: bool
    valid: bool
    reason: str | None = None
    metadata: dict[str, int | float | str] = field(default_factory=dict)


class Indicator(Protocol):
    """Contract implemented by each independently calculable indicator."""

    @property
    def name(self) -> str:
        """Return the stable indicator name."""

    def calculate(self, data: pl.DataFrame) -> IndicatorResult:
        """Calculate the indicator from canonical OHLCV data."""


class BaseIndicator:
    """Common validation and structured logging for indicator implementations."""

    @property
    def name(self) -> str:
        """Return the stable indicator name."""
        raise NotImplementedError

    def _validation_error(
        self,
        data: pl.DataFrame,
        *,
        required_columns: frozenset[str],
        minimum_history: int,
    ) -> str | None:
        missing_columns = required_columns.difference(data.columns)
        if missing_columns:
            return f"Missing required columns: {sorted(missing_columns)}."
        if data.height < minimum_history:
            return f"Requires at least {minimum_history} rows."
        for column in required_columns:
            series = data.get_column(column)
            if series.null_count() > 0:
                return f"Column '{column}' contains null values."
            try:
                invalid = data.select(
                    (
                        pl.col(column).cast(pl.Float64, strict=False).is_null()
                        | (pl.col(column).cast(pl.Float64, strict=False) <= 0)
                        | pl.col(column).cast(pl.Float64, strict=False).is_nan()
                    ).any()
                ).item()
            except pl.exceptions.PolarsError:
                return f"Column '{column}' contains invalid prices."
            if invalid:
                return f"Column '{column}' contains invalid prices."
        return None

    def _result(
        self,
        *,
        value: float | None,
        valid: bool,
        reason: str | None,
        rows: int,
        started_at: float,
        metadata: dict[str, int | float | str],
    ) -> IndicatorResult:
        duration_ms = (perf_counter() - started_at) * 1_000
        logger.info(
            "indicator_calculated",
            indicator=self.name,
            rows=rows,
            duration_ms=round(duration_ms, 3),
            status="OK" if valid else "INVALID",
        )
        return IndicatorResult(
            name=self.name,
            value=value,
            warmup_complete=valid,
            valid=valid,
            reason=reason,
            metadata=metadata,
        )
