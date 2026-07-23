"""Provider interfaces and plugin discovery."""

from pie.providers.interfaces import MarketDataProvider, PortfolioProvider, Provider, TrendProvider
from pie.providers.registry import discover_providers
from pie.providers.yahoo import HTTPClient, HTTPResponse, UrllibHTTPClient, YahooFinanceProvider

__all__ = [
    "HTTPClient",
    "HTTPResponse",
    "MarketDataProvider",
    "PortfolioProvider",
    "Provider",
    "TrendProvider",
    "UrllibHTTPClient",
    "YahooFinanceProvider",
    "discover_providers",
]
