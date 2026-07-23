"""Relative strength index indicator."""

from dataclasses import dataclass
from time import perf_counter

import polars as pl

from pie.market.indicators.base import BaseIndicator, IndicatorResult


@dataclass(frozen=True, slots=True)
class RSI(BaseIndicator):
    """Calculate Wilder's relative strength index from closing prices."""

    period: int = 14

    @property
    def name(self) -> str:
        """Return the stable indicator name."""
        return f"RSI({self.period})"

    def calculate(self, data: pl.DataFrame) -> IndicatorResult:
        """Calculate the latest RSI value."""
        started_at = perf_counter()
        validation_error = self._validation_error(
            data,
            required_columns=frozenset({"close"}),
            minimum_history=self.period + 1,
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
            change = pl.col("close").diff().fill_null(0.0)
            average_gain = change.clip(lower_bound=0.0).ewm_mean(
                alpha=1 / self.period,
                adjust=False,
            )
            average_loss = (-change.clip(upper_bound=0.0)).ewm_mean(
                alpha=1 / self.period,
                adjust=False,
            )
            value = data.select(
                pl.when((average_gain == 0) & (average_loss == 0))
                .then(50.0)
                .when(average_loss == 0)
                .then(100.0)
                .otherwise(100.0 - (100.0 / (1.0 + (average_gain / average_loss))))
                .last()
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
                reason="Unable to calculate RSI.",
                rows=data.height,
                started_at=started_at,
                metadata={"period": self.period},
            )
