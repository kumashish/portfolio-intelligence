"""Stateful historical evaluation of the trend engine's directional signals."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

import polars as pl
import structlog

from pie.core.models import MarketSnapshot
from pie.market.backtest.models import BacktestReport, BacktestTrade, SignalDirection
from pie.market.indicators.engine import IndicatorEngine
from pie.market.trend.engine import TrendEngine
from pie.market.trend.models import MarketRegime

logger = structlog.get_logger(__name__)

MINIMUM_HISTORY = 200


@dataclass(frozen=True, slots=True)
class TrendBacktester:
    """Backtest long and short directional signals emitted by TrendEngine."""

    indicator_engine: IndicatorEngine
    trend_engine: TrendEngine
    maximum_hold_days: int = 37

    def run(self, symbol: str, data: pl.DataFrame) -> BacktestReport:
        """Evaluate historical signals without modelling option-contract pricing."""
        self._validate_data(data)
        trades: list[BacktestTrade] = []
        active_trade: tuple[SignalDirection, datetime, float, MarketRegime] | None = None
        ordered_data = data.sort("timestamp")
        for index in range(MINIMUM_HISTORY - 1, ordered_data.height):
            history = ordered_data.slice(0, index + 1)
            timestamp, price = self._latest_price(history)
            analysis = self.trend_engine.analyze(
                MarketSnapshot(
                    symbol=symbol,
                    observed_at=timestamp,
                    last_price=Decimal(str(price)),
                ),
                self.indicator_engine.calculate(history),
                history,
            )
            direction = self._direction(analysis.regime)
            if active_trade is None and direction is not None:
                active_trade = (direction, timestamp, price, analysis.regime)
                continue
            if active_trade is None:
                continue
            entry_direction, entry_at, entry_price, entry_regime = active_trade
            held_days = (timestamp.date() - entry_at.date()).days
            reversed_signal = direction is not entry_direction
            if held_days >= self.maximum_hold_days or reversed_signal:
                exit_reason = (
                    "maximum_hold" if held_days >= self.maximum_hold_days else "regime_reversal"
                )
                trades.append(
                    self._close_trade(
                        entry_direction,
                        entry_at,
                        entry_price,
                        entry_regime,
                        timestamp,
                        price,
                        exit_reason,
                    )
                )
                active_trade = None
        if active_trade is not None:
            direction, entry_at, entry_price, entry_regime = active_trade
            exit_at, exit_price = self._latest_price(ordered_data)
            trades.append(
                self._close_trade(
                    direction,
                    entry_at,
                    entry_price,
                    entry_regime,
                    exit_at,
                    exit_price,
                    "end_of_data",
                )
            )
        report = self._report(symbol, tuple(trades))
        logger.info(
            "trend_backtest_completed",
            symbol=symbol,
            trades=len(report.trades),
            win_rate=report.win_rate,
            average_return_percent=report.average_return_percent,
        )
        return report

    @staticmethod
    def _validate_data(data: pl.DataFrame) -> None:
        required_columns = {"timestamp", "open", "high", "low", "close"}
        missing_columns = required_columns.difference(data.columns)
        if missing_columns or data.height < MINIMUM_HISTORY:
            msg = f"Backtesting requires {MINIMUM_HISTORY} valid OHLC rows."
            raise ValueError(msg)

    @staticmethod
    def _latest_price(data: pl.DataFrame) -> tuple[datetime, float]:
        timestamp = data.get_column("timestamp").tail(1).item()
        price = data.get_column("close").tail(1).item()
        if not isinstance(timestamp, datetime) or not isinstance(price, (float, int)):
            msg = "Backtest data must contain datetime timestamps and numeric close prices."
            raise ValueError(msg)
        return timestamp, float(price)

    @staticmethod
    def _direction(regime: MarketRegime) -> SignalDirection | None:
        if regime in {MarketRegime.STRONG_BULL, MarketRegime.BULL}:
            return SignalDirection.LONG
        if regime in {MarketRegime.STRONG_BEAR, MarketRegime.BEAR}:
            return SignalDirection.SHORT
        return None

    @staticmethod
    def _close_trade(
        direction: SignalDirection,
        entry_at: datetime,
        entry_price: float,
        entry_regime: MarketRegime,
        exit_at: datetime,
        exit_price: float,
        exit_reason: str,
    ) -> BacktestTrade:
        multiplier = 1.0 if direction is SignalDirection.LONG else -1.0
        return BacktestTrade(
            direction=direction,
            entry_at=entry_at,
            exit_at=exit_at,
            entry_price=entry_price,
            exit_price=exit_price,
            return_percent=round(multiplier * ((exit_price / entry_price) - 1.0) * 100.0, 2),
            entry_regime=entry_regime,
            exit_reason=exit_reason,
        )

    def _report(self, symbol: str, trades: tuple[BacktestTrade, ...]) -> BacktestReport:
        returns = [trade.return_percent for trade in trades]
        win_rate = (
            sum(return_value > 0.0 for return_value in returns) / len(returns) if returns else 0.0
        )
        average_return = sum(returns) / len(returns) if returns else 0.0
        cumulative_return = sum(returns)
        peak = 0.0
        equity = 0.0
        drawdown = 0.0
        for return_value in returns:
            equity += return_value
            peak = max(peak, equity)
            drawdown = min(drawdown, equity - peak)
        return BacktestReport(
            symbol=symbol,
            trades=trades,
            win_rate=round(win_rate, 4),
            average_return_percent=round(average_return, 2),
            cumulative_return_percent=round(cumulative_return, 2),
            maximum_drawdown_percent=round(drawdown, 2),
            assumptions=(
                "Signal-level index backtest; not option-spread P&L.",
                "Entries use Bull/Strong Bull for long and Bear/Strong Bear for short exposure.",
                f"Maximum holding period is {self.maximum_hold_days} calendar days.",
                "Positions exit on regime reversal, maximum hold, or end of data.",
            ),
        )
