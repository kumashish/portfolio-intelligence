"""Maintain a single combined market snapshot JSON used to render the README table."""

import json
from pathlib import Path

CANONICAL_SYMBOL_ORDER = ["^NSEI", "^NSEBANK", "SPY", "QQQ"]


def _sort_key(entry: dict[str, str]) -> tuple[int, str]:
    symbol = entry.get("symbol", "")
    try:
        return CANONICAL_SYMBOL_ORDER.index(symbol), symbol
    except ValueError:
        return len(CANONICAL_SYMBOL_ORDER), symbol


def upsert_snapshot_entry(snapshot_path: Path, entry: dict[str, str]) -> list[dict[str, str]]:
    """Insert or replace the row for entry['symbol'] in the snapshot JSON file.

    Returns the full, sorted list of entries after the update.
    """
    existing: list[dict[str, str]] = []
    if snapshot_path.exists():
        try:
            existing = json.loads(snapshot_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            existing = []

    existing = [row for row in existing if row.get("symbol") != entry["symbol"]]
    existing.append(entry)
    existing.sort(key=_sort_key)

    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    return existing
