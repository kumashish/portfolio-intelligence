"""Domain-specific failures raised by the market data layer."""


class MarketDataError(Exception):
    """Base exception for market data operations."""


class ProviderUnavailable(MarketDataError):
    """Raised when a market data provider cannot serve a request."""


class ValidationError(MarketDataError):
    """Raised when market data does not meet pipeline requirements."""


class SnapshotError(MarketDataError):
    """Raised when valid data cannot be converted into snapshots."""
