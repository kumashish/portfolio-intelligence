#!/usr/bin/env python3
"""Update README.md market snapshot table from market_snapshot.json."""

import json
import re
from pathlib import Path


def load_market_data(json_path: str = "market_snapshot.json") -> list[dict]:
    """Load market data from JSON file."""
    try:
        with open(json_path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def format_market_table(markets: list[dict]) -> str:
    """Format market data as Markdown table."""
    if not markets:
        return "<!-- MARKET-SNAPSHOT-START -->\n<!-- MARKET-SNAPSHOT-END -->"
    
    # Build table header and rows
    lines = ["<!-- MARKET-SNAPSHOT-START -->"]
    lines.append("| Market    | Updated   | Trend      | Strategy          | Signal | Since  |")
    lines.append("| --------- | --------- | ---------- | ----------------- | ------ | ------ |")
    
    for market in markets:
        market_name = market.get("market", "")
        updated = market.get("updated", "")
        trend = market.get("trend", "")
        strategy = market.get("strategy", "")
        signal = market.get("signal", "")
        since = market.get("since", "")
        
        # Pad columns for alignment
        line = f"| {market_name:<9} | {updated:<9} | {trend:<10} | {strategy:<17} | {signal:<6} | {since:<6} |"
        lines.append(line)
    
    lines.append("<!-- MARKET-SNAPSHOT-END -->")
    return "\n".join(lines)


def update_readme(readme_path: str = "README.md"):
    """Update README.md with new market snapshot."""
    readme = Path(readme_path)
    if not readme.exists():
        print(f"{readme_path} not found")
        return
    
    content = readme.read_text()
    markets = load_market_data()
    new_table = format_market_table(markets)
    
    # Replace content between markers
    pattern = r"<!-- MARKET-SNAPSHOT-START -->.*?<!-- MARKET-SNAPSHOT-END -->"
    updated_content = re.sub(pattern, new_table, content, flags=re.DOTALL)
    
    readme.write_text(updated_content)
    print(f"Updated {readme_path} with {len(markets)} market entries")


if __name__ == "__main__":
    update_readme()
