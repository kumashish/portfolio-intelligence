"""Yahoo Finance implementation of the market-data provider contract."""

from collections.abc import Mapping
from typing import Any, Protocol

import polars as pl
import structlog

from pie.market_data.exceptions import MarketDataError, ProviderUnavailable
from pie.providers.interfaces import MarketDataProvider

logger = structlog.get_logger(__name__)

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart"


class HTTPResponse(Protocol):
    """Minimal HTTP response contract required by YahooFinanceProvider."""

    @property
    def status_code(self) -> int:
        """Return the HTTP status code."""

    def json(self) -> object:
        """Decode the response body as JSON."""


class HTTPClient(Protocol):
    """Minimal injected HTTP client contract."""

    def get(self, url: str, *, params: Mapping[str, str]) -> HTTPResponse:
        """Issue an HTTP GET request."""


class YahooFinanceProvider(MarketDataProvider):
    """Retrieve Yahoo Finance chart data through an injected HTTP client."""

    def __init__(self, http_client: HTTPClient) -> None:
        self._http_client = http_client

    @property
    def name(self) -> str:
        """Return the provider registration name."""
        return "yahoo_finance"

    def fetch_history(self, symbol: str, *, period: str, interval: str) -> pl.DataFrame:
        """Fetch and normalize Yahoo chart data into canonical OHLCV columns."""
        log = logger.bind(provider=self.name, symbol=symbol, period=period, interval=interval)
        try:
            response = self._http_client.get(
                f"{YAHOO_CHART_URL}/{symbol}",
                params={"range": period, "interval": interval},
            )
        except Exception as error:
            log.warning("market_data_provider_unavailable", exc_info=True)
            msg = f"Yahoo Finance is unavailable for '{symbol}'."
            raise ProviderUnavailable(msg) from error
        if response.status_code != 200:
            log.warning("market_data_provider_unavailable", status_code=response.status_code)
            msg = f"Yahoo Finance returned HTTP {response.status_code} for '{symbol}'."
            raise ProviderUnavailable(msg)
        try:
            data = self._normalize(response.json())
        except (KeyError, TypeError, ValueError) as error:
            log.warning("market_data_provider_invalid_response", exc_info=True)
            msg = f"Yahoo Finance returned invalid chart data for '{symbol}'."
            raise MarketDataError(msg) from error
        log.info("market_data_fetched", rows=data.height)
        return data

    @staticmethod
    def _normalize(payload: object) -> pl.DataFrame:
        if not isinstance(payload, dict):
            raise TypeError("Expected a JSON object.")
        chart = payload["chart"]
        if not isinstance(chart, dict):
            raise TypeError("Expected a chart object.")
        result = chart["result"]
        if not isinstance(result, list) or len(result) != 1 or not isinstance(result[0], dict):
            raise ValueError("Expected one chart result.")
        chart_result: dict[str, Any] = result[0]
        timestamps = chart_result["timestamp"]
        indicators = chart_result["indicators"]
        if not isinstance(timestamps, list) or not isinstance(indicators, dict):
            raise TypeError("Expected timestamps and indicators.")
        quote = indicators["quote"]
        if not isinstance(quote, list) or len(quote) != 1 or not isinstance(quote[0], dict):
            raise ValueError("Expected one quote payload.")
        quote_data: dict[str, Any] = quote[0]
        data = pl.DataFrame(
            {
                "timestamp": timestamps,
                "open": quote_data["open"],
                "high": quote_data["high"],
                "low": quote_data["low"],
                "close": quote_data["close"],
                "volume": quote_data["volume"],
            }
        )
        return data.with_columns(
            pl.from_epoch(pl.col("timestamp").cast(pl.Int64), time_unit="s").alias("timestamp")
        )
