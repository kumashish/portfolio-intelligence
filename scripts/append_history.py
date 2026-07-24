#!/usr/bin/env python3
"""
Append current signal to history file.
"""
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

HISTORY_DIR = Path("reports/history")
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

symbol_map = {
    "^NSEI": "NIFTY 50",
    "^NSEBANK": "BANKNIFTY",
    "SPY": "SPY",
    "QQQ": "QQQ",
}

def main():
    if len(sys.argv) < 5:
        print("Usage: append_history.py <symbol> <trend> <strategy> <signal> [note]")
        sys.exit(1)
    
    symbol = sys.argv[1]
    trend = sys.argv[2]
    strategy = sys.argv[3]
    signal = sys.argv[4]
    note = sys.argv[5] if len(sys.argv) > 5 else ""
    
    display_name = symbol_map.get(symbol, symbol)
    hist_file = HISTORY_DIR / f"{display_name}.json"
    
    # Load existing history
    history = []
    if hist_file.exists():
        with open(hist_file, "r") as f:
            history = json.load(f)
        if not isinstance(history, list):
            history = [history]
    
    # Determine timezone based on market
    ist_markets = {"NIFTY 50", "BANKNIFTY", "^NSEI", "^NSEBANK"}
    if display_name in ist_markets or symbol.startswith("^NSE"):
        tz = timezone(timedelta(hours=5, minutes=30))
    else:
        tz = timezone.utc
    
    # Append new entry
    new_entry = {
        "timestamp": datetime.now(tz).isoformat(),
        "trend": trend,
        "strategy": strategy,
        "signal": signal,
        "note": note,
    }
    
    history.append(new_entry)
    
    # Keep only last 50 entries
    history = history[-50:]
    
    with open(hist_file, "w") as f:
        json.dump(history, f, indent=2)
    
    print(f"✅ Appended history for {display_name} ({len(history)} total entries)")


if __name__ == "__main__":
    main()
