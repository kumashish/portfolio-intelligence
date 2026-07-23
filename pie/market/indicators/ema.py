"""Exponential moving average indicator."""

from dataclasses import dataclass
from time import perf_counter

import polars as pl

from pie.market.indicators.base import BaseIndicator, IndicatorResult


@dataclass(frozen=True, slots=True)
class EMA(BaseIndicator):
    """Calculate an exponential moving average of closing prices."""

    period: int

    @property
    def name(self) -> str:
        """Return the stable indicator name."""
        return f"EMA{self.period}"

    def calculate(self, data: pl.DataFrame) -> IndicatorResult:
        """Calculate the latest EMA value."""
        started_at = perf_counter()
        validation_error = self._validation_error(
            data,
            required_columns=frozenset({"close"}),
            minimum_history=self.period,
        )
        if validation_error:
            return self._result(
                value=None,
                valid=False,
                reason=validation_error,
                rows=data.height,
                started_at=started_at,
                metadata={"period": self.period},
            )
        try:
            value = data.select(
                pl.col("close").ewm_mean(alpha=2 / (self.period + 1), adjust=False).last()
            ).item()
            return self._result(
                value=float(value),
                valid=True,
                reason=None,
                rows=data.height,
                started_at=started_at,
                metadata={"period": self.period},
            )
        except (TypeError, ValueError, pl.exceptions.PolarsError):
            return self._result(
                value=None,
                valid=False,
                reason="Unable to calculate EMA.",
                rows=data.height,
                started_at=started_at,
                metadata={"period": self.period},
            )
