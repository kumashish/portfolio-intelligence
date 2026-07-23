"""Average true range indicator."""

from dataclasses import dataclass
from time import perf_counter

import polars as pl

from pie.market.indicators.base import BaseIndicator, IndicatorResult


@dataclass(frozen=True, slots=True)
class ATR(BaseIndicator):
    """Calculate Wilder's average true range."""

    period: int = 14

    @property
    def name(self) -> str:
        """Return the stable indicator name."""
        return f"ATR({self.period})"

    def calculate(self, data: pl.DataFrame) -> IndicatorResult:
        """Calculate the latest ATR value."""
        started_at = perf_counter()
        validation_error = self._validation_error(
            data,
            required_columns=frozenset({"high", "low", "close"}),
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
            previous_close = pl.col("close").shift(1).fill_null(pl.col("close"))
            true_range = pl.max_horizontal(
                pl.col("high") - pl.col("low"),
                (pl.col("high") - previous_close).abs(),
                (pl.col("low") - previous_close).abs(),
            )
            value = data.select(
                true_range.ewm_mean(alpha=1 / self.period, adjust=False).last()
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
                reason="Unable to calculate ATR.",
                rows=data.height,
                started_at=started_at,
                metadata={"period": self.period},
            )
