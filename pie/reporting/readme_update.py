"""Generate market snapshot for README with IST timestamps."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TypedDict


class MarketRow(TypedDict):
    """Market snapshot row for README table."""

    symbol: str
    market: str
    updated: str  # "HH:MM IST" or "HH:MM IST (YYYY-MM-DD)"
    trend: str
    strategy: str
    signal: str
    since: str  # "N days (YYYY-MM-DD HH:MM IST)"


def utc_to_ist(dt: datetime) -> datetime:
    """Convert UTC datetime to IST (UTC+5:30)."""
    ist_offset = timedelta(hours=5, minutes=30)
    return dt.astimezone(UTC).replace(tzinfo=None) + ist_offset


def format_ist_time(dt: datetime, include_date: bool = False) -> str:
    """Format datetime as IST time string.

    Args:
        dt: datetime object (can be in any timezone, will be converted to IST)
        include_date: if True, include date in output
    """
    ist_dt = utc_to_ist(dt) if dt.tzinfo else dt
    if include_date:
        return ist_dt.strftime("%H:%M IST (%Y-%m-%d)")
    return ist_dt.strftime("%H:%M IST")


def calculate_since(
    signal_date: datetime, current_time: datetime | None = None
) -> tuple[str, datetime]:
    """Calculate 'since' duration and format it.

    Args:
        signal_date: when the signal was activated
        current_time: reference time (defaults to now)

    Returns:
        Tuple of (formatted_string, signal_date_in_ist)
    """
    if current_time is None:
        current_time = datetime.now(UTC)

    signal_ist = utc_to_ist(signal_date)
    current_ist = utc_to_ist(current_time)

    delta_days = (current_ist.date() - signal_ist.date()).days

    if delta_days == 0:
        return "Today", signal_ist
    elif delta_days == 1:
        return "Yesterday", signal_ist
    else:
        return f"{delta_days} days", signal_ist


def generate_readme_snapshot(
    market_data: list[dict],
    current_time: datetime | None = None,
) -> str:
    """Generate markdown table rows for README.

    Args:
        market_data: list of dicts with keys:
            - symbol: stock symbol (e.g., "^NSEI", "SPY")
            - market: market name (e.g., "NIFTY 50", "SPY")
            - last_updated: datetime of last analysis (UTC)
            - trend: trend emoji and label (e.g., "🟢 Bull")
            - strategy: strategy name
            - signal: signal status (e.g., "NEW", "Active", "Hold")
            - signal_since: datetime when signal started (UTC)
        current_time: reference time for calculations

    Returns:
        Markdown table rows as string
    """
    if current_time is None:
        current_time = datetime.now(UTC)

    rows = ["| Market    | Updated   | Trend      | Strategy          | Signal | Since  |"]
    rows.append("| --------- | --------- | ---------- | ----------------- | ------ | ------ |")

    for data in market_data:
        market = data["market"]
        updated_time = format_ist_time(data["last_updated"], include_date=False)
        trend = data["trend"]
        strategy = data["strategy"]
        signal = data["signal"]

        since_text, signal_ist = calculate_since(data["signal_since"], current_time)
        since_full = f"{since_text} ({signal_ist.strftime('%Y-%m-%d %H:%M IST')})"

        row = f"| {market:<9} | {updated_time:<9} | {trend:<10} | {strategy:<17} | {signal:<6} | {since_full:<29} |"
        rows.append(row)

    return "\n".join(rows)


def update_readme_snapshot(
    readme_path: Path,
    market_data: list[dict],
    current_time: datetime | None = None,
) -> bool:
    """Update README.md with new market snapshot table.

    Args:
        readme_path: path to README.md
        market_data: list of market data dicts
        current_time: reference time for calculations

    Returns:
        True if file was modified, False otherwise
    """
    if not readme_path.exists():
        raise FileNotFoundError(f"README not found at {readme_path}")

    readme_content = readme_path.read_text(encoding="utf-8")
    new_table = generate_readme_snapshot(market_data, current_time)

    # Find and replace the snapshot section
    start_marker = "<!-- MARKET-SNAPSHOT-START -->"
    end_marker = "<!-- MARKET-SNAPSHOT-END -->"

    if start_marker not in readme_content or end_marker not in readme_content:
        raise ValueError("README missing MARKET-SNAPSHOT markers")

    start_idx = readme_content.find(start_marker)
    end_idx = readme_content.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        raise ValueError("Could not find snapshot markers in README")

    # Preserve the markers and content before/after
    new_content = (
        readme_content[: start_idx + len(start_marker)]
        + "\n"
        + new_table
        + "\n"
        + readme_content[end_idx:]
    )

    # Check if content actually changed
    if new_content == readme_content:
        return False

    readme_path.write_text(new_content, encoding="utf-8")
    return True


def load_market_data_from_json(json_file: Path) -> list[dict]:
    """Load market data from JSON file.

    JSON format:
    [
        {
            "symbol": "^NSEI",
            "market": "NIFTY 50",
            "last_updated": "2024-01-15T15:20:00Z",
            "trend": "🟢 Bull",
            "strategy": "Call Debit Spread",
            "signal": "NEW",
            "signal_since": "2024-01-15T15:20:00Z"
        },
        ...
    ]
    """
    with open(json_file, encoding="utf-8") as f:
        raw_data = json.load(f)

    # Convert ISO timestamp strings to datetime objects
    for row in raw_data:
        row["last_updated"] = datetime.fromisoformat(row["last_updated"].replace("Z", "+00:00"))
        row["signal_since"] = datetime.fromisoformat(
            row["signal_since"].replace("Z", "+00:00")
        )

    return raw_data
