"""Historical evaluation of quantitative trend signals."""

from pie.market.backtest.engine import TrendBacktester
from pie.market.backtest.models import BacktestReport, BacktestTrade

__all__ = ["BacktestReport", "BacktestTrade", "TrendBacktester"]
