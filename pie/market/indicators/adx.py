"""Average directional index indicator."""

from dataclasses import dataclass
from time import perf_counter

import polars as pl

from pie.market.indicators.base import BaseIndicator, IndicatorResult


@dataclass(frozen=True, slots=True)
class ADX(BaseIndicator):
    """Calculate Wilder's average directional index."""

    period: int = 14

    @property
    def name(self) -> str:
        """Return the stable indicator name."""
        return f"ADX({self.period})"

    def calculate(self, data: pl.DataFrame) -> IndicatorResult:
        """Calculate the latest ADX value."""
        started_at = perf_counter()
        validation_error = self._validation_error(
            data,
            required_columns=frozenset({"high", "low", "close"}),
            minimum_history=(self.period * 2) - 1,
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
            high = pl.col("high")
            low = pl.col("low")
            close = pl.col("close")
            previous_close = close.shift(1).fill_null(close)
            up_move = (high - high.shift(1)).fill_null(0.0)
            down_move = (low.shift(1) - low).fill_null(0.0)
            plus_directional_movement = (
                pl.when((up_move > down_move) & (up_move > 0.0)).then(up_move).otherwise(0.0)
            )
            minus_directional_movement = (
                pl.when((down_move > up_move) & (down_move > 0.0)).then(down_move).otherwise(0.0)
            )
            true_range = pl.max_horizontal(
                high - low,
                (high - previous_close).abs(),
                (low - previous_close).abs(),
            )
            average_true_range = true_range.ewm_mean(alpha=1 / self.period, adjust=False)
            plus_directional_index = (
                pl.when(average_true_range > 0.0)
                .then(
                    100.0
                    * plus_directional_movement.ewm_mean(alpha=1 / self.period, adjust=False)
                    / average_true_range
                )
                .otherwise(0.0)
            )
            minus_directional_index = (
                pl.when(average_true_range > 0.0)
                .then(
                    100.0
                    * minus_directional_movement.ewm_mean(alpha=1 / self.period, adjust=False)
                    / average_true_range
                )
                .otherwise(0.0)
            )
            directional_index_sum = plus_directional_index + minus_directional_index
            directional_index = (
                pl.when(directional_index_sum > 0.0)
                .then(
                    100.0
                    * (plus_directional_index - minus_directional_index).abs()
                    / directional_index_sum
                )
                .otherwise(0.0)
            )
            value = data.select(
                directional_index.ewm_mean(alpha=1 / self.period, adjust=False).last()
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
                reason="Unable to calculate ADX.",
                rows=data.height,
                started_at=started_at,
                metadata={"period": self.period},
            )
