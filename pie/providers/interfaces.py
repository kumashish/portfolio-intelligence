"""Abstract contracts implemented by external data providers."""

from abc import ABC, abstractmethod

import polars as pl

from pie.core.models import PortfolioSnapshot
from pie.market.trend.models import TrendAnalysis


class Provider(ABC):
    """Base contract for a pluggable provider."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider's stable registration name."""


class MarketDataProvider(Provider):
    """Supplies canonical OHLCV market history."""

    @abstractmethod
    def fetch_history(self, symbol: str, *, period: str, interval: str) -> pl.DataFrame:
        """Fetch market history for a symbol as a Polars DataFrame."""


class PortfolioProvider(Provider):
    """Supplies account portfolio snapshots."""

    @abstractmethod
    def fetch_portfolio_snapshot(self, account_id: str) -> PortfolioSnapshot:
        """Fetch the current snapshot for an account."""


class TrendProvider(Provider):
    """Supplies trend analyses."""

    @abstractmethod
    def analyze_trend(self, symbol: str) -> TrendAnalysis:
        """Analyze the trend for a symbol."""
