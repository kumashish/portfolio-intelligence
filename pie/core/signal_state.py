"""Persistent state tracking for market signals."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class SignalState(BaseModel):
    """Persistent state for a market signal."""

    symbol: str
    last_strategy: str
    last_regime: str
    trend_started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(UTC))
    signal_age_sessions: int = 0

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return {
            "symbol": self.symbol,
            "last_strategy": self.last_strategy,
            "last_regime": self.last_regime,
            "trend_started_at": self.trend_started_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "signal_age_sessions": self.signal_age_sessions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SignalState":
        """Deserialize from JSON dict."""
        return cls(
            symbol=data["symbol"],
            last_strategy=data["last_strategy"],
            last_regime=data["last_regime"],
            trend_started_at=datetime.fromisoformat(data["trend_started_at"]),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            signal_age_sessions=data.get("signal_age_sessions", 0),
        )


class SignalStateManager:
    """Manages persistence of signal state files."""

    def __init__(self, state_dir: Path = Path("state")):
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _get_state_path(self, symbol: str) -> Path:
        """Get state file path for a symbol."""
        safe_symbol = symbol.replace("^", "").replace("/", "_")
        return self.state_dir / f"{safe_symbol}.json"

    def load_state(self, symbol: str) -> Optional[SignalState]:
        """Load previous state for a symbol, or None if not found."""
        state_path = self._get_state_path(symbol)
        if not state_path.exists():
            return None
        try:
            data = json.loads(state_path.read_text(encoding="utf-8"))
            return SignalState.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def save_state(self, state: SignalState) -> None:
        """Save state for a symbol."""
        state_path = self._get_state_path(state.symbol)
        state_path.write_text(
            json.dumps(state.to_dict(), indent=2),
            encoding="utf-8",
        )

    def update_state(
        self,
        symbol: str,
        strategy: str,
        regime: str,
    ) -> tuple[SignalState, str]:
        """
        Update state and return (new_state, status).

        Status can be: "NEW", "CHANGED", or "EXISTING"
        """
        previous = self.load_state(symbol)
        now = datetime.now(UTC)

        if previous is None:
            # First time seeing this signal
            state = SignalState(
                symbol=symbol,
                last_strategy=strategy,
                last_regime=regime,
                trend_started_at=now,
                last_updated=now,
                signal_age_sessions=1,
            )
            self.save_state(state)
            return state, "NEW"

        # Check if anything changed
        strategy_changed = strategy != previous.last_strategy
        regime_changed = regime != previous.last_regime

        if strategy_changed or regime_changed:
            # Signal has changed
            state = SignalState(
                symbol=symbol,
                last_strategy=strategy,
                last_regime=regime,
                trend_started_at=now,
                last_updated=now,
                signal_age_sessions=1,
            )
            self.save_state(state)
            return state, "CHANGED"

        # No change — increment age
        state = SignalState(
            symbol=symbol,
            last_strategy=strategy,
            last_regime=regime,
            trend_started_at=previous.trend_started_at,
            last_updated=now,
            signal_age_sessions=previous.signal_age_sessions + 1,
        )
        self.save_state(state)
        return state, "EXISTING"
