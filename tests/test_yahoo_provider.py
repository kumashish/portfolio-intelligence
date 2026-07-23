from collections.abc import Mapping
from typing import Any

import pytest

from pie.market_data.exceptions import MarketDataError, ProviderUnavailable
from pie.providers.yahoo import HTTPResponse, YahooFinanceProvider


class MockResponse:
    def __init__(self, status_code: int, payload: object) -> None:
        self._status_code = status_code
        self._payload = payload

    @property
    def status_code(self) -> int:
        return self._status_code

    def json(self) -> object:
        return self._payload


class MockHTTPClient:
    def __init__(self, response: HTTPResponse) -> None:
        self.response = response
        self.request: tuple[str, Mapping[str, str]] | None = None

    def get(self, url: str, *, params: Mapping[str, str]) -> HTTPResponse:
        self.request = (url, params)
        return self.response


def yahoo_payload() -> dict[str, Any]:
    return {
        "chart": {
            "result": [
                {
                    "timestamp": [1_704_067_200, 1_704_153_600],
                    "indicators": {
                        "quote": [
                            {
                                "open": [470.0, 471.0],
                                "high": [472.0, 473.0],
                                "low": [469.0, 470.0],
                                "close": [471.0, 472.0],
                                "volume": [100, 200],
                            }
                        ]
                    },
                }
            ]
        }
    }


def test_yahoo_provider_normalizes_mocked_response() -> None:
    client = MockHTTPClient(MockResponse(200, yahoo_payload()))

    data = YahooFinanceProvider(client).fetch_history("SPY", period="5d", interval="1d")

    assert data.columns == ["timestamp", "open", "high", "low", "close", "volume"]
    assert data.height == 2
    assert client.request is not None
    assert client.request[1] == {"range": "5d", "interval": "1d"}


def test_yahoo_provider_wraps_unavailable_response() -> None:
    provider = YahooFinanceProvider(MockHTTPClient(MockResponse(503, {})))

    with pytest.raises(ProviderUnavailable, match="HTTP 503"):
        provider.fetch_history("SPY", period="5d", interval="1d")


def test_yahoo_provider_rejects_invalid_payload() -> None:
    provider = YahooFinanceProvider(MockHTTPClient(MockResponse(200, {})))

    with pytest.raises(MarketDataError, match="invalid chart data"):
        provider.fetch_history("SPY", period="5d", interval="1d")
