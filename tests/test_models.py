from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from pie.core.models import (
    MarketSnapshot,
    PortfolioSnapshot,
    Position,
    PositionSide,
)


def test_domain_models_are_immutable() -> None:
    snapshot = MarketSnapshot(
        symbol="SPY",
        observed_at=datetime.now(UTC),
        last_price=Decimal("600.00"),
    )

    with pytest.raises(ValidationError):
        snapshot.symbol = "QQQ"


def test_portfolio_snapshot_accepts_immutable_positions() -> None:
    position = Position(
        symbol="SPY",
        quantity=Decimal("1"),
        average_cost=Decimal("600.00"),
        market_value=Decimal("610.00"),
        side=PositionSide.LONG,
    )

    snapshot = PortfolioSnapshot(
        account_id="demo",
        observed_at=datetime.now(UTC),
        net_liquidation_value=Decimal("10000.00"),
        cash_balance=Decimal("9390.00"),
        positions=(position,),
    )

    assert snapshot.positions == (position,)
