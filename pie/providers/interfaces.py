"""Abstract contracts implemented by external data providers."""

from abc import ABC, abstractmethod

from pie.core.models import MarketSnapshot, PortfolioSnapshot, TrendAnalysis


class Provider(ABC):
    """Base contract for a pluggable provider."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider's stable registration name."""


class MarketDataProvider(Provider):
    """Supplies market snapshots."""

    @abstractmethod
    def fetch_market_snapshot(self, symbol: str) -> MarketSnapshot:
        """Fetch the current market snapshot for a symbol."""


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
