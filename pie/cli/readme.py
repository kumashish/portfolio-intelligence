"""CLI commands for generating and updating README market snapshot."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer

from pie.reporting.readme_update import (
    generate_readme_snapshot,
    load_market_data_from_json,
    update_readme_snapshot,
)

readme_app = typer.Typer(help="README update commands.", no_args_is_help=True)


@readme_app.command("generate-snapshot-metadata")
def generate_snapshot_metadata(
    output: Annotated[Path, typer.Option(help="Output JSON file path.")] = Path(
        "reports/market/snapshot.json"
    ),
    symbols: Annotated[
        list[str], typer.Option(help="Market symbols to include (repeatable).")
    ] = ["^NSEI", "^NSEBANK", "SPY", "QQQ"],
) -> None:
    """Generate market snapshot metadata from latest report files.

    Scans reports/market/ directory for the most recent analysis files
    and generates a JSON metadata file with IST-formatted timestamps.
    """
    import json
    from glob import glob

    # Map symbols to market names
    symbol_names = {
        "^NSEI": "NIFTY 50",
        "^NSEBANK": "BANKNIFTY",
        "SPY": "SPY",
        "QQQ": "QQQ",
    }

    # Placeholder implementation - in production, would parse actual report files
    market_data = []
    now = datetime.now(UTC)

    for symbol in symbols:
        market_data.append(
            {
                "symbol": symbol,
                "market": symbol_names.get(symbol, symbol),
                "last_updated": now.isoformat(),
                "trend": "🟢 Bull",  # Would be parsed from report
                "strategy": "Call Debit Spread",  # Would be parsed from report
                "signal": "NEW",  # Would be parsed from report
                "signal_since": now.isoformat(),  # Would be parsed from report
            }
        )

    # In a real scenario, you'd read from actual report files:
    # reports_dir = Path("reports/market")
    # for symbol in symbols:
    #     latest_report = max(
    #         glob(str(reports_dir / f"{symbol}_*.txt")),
    #         key=lambda x: Path(x).stat().st_mtime,
    #         default=None
    #     )
    #     if latest_report:
    #         # Parse the report file and extract metadata
    #         ...

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(market_data, indent=2), encoding="utf-8")
    typer.echo(f"Generated snapshot metadata: {output}")


@readme_app.command("update-readme-snapshot")
def update_readme_snapshot_cmd(
    snapshot_file: Annotated[
        Path, typer.Option(help="Path to snapshot JSON metadata file.")
    ] = Path("reports/market/snapshot.json"),
    readme: Annotated[Path, typer.Option(help="Path to README.md file.")] = Path(
        "README.md"
    ),
) -> None:
    """Update README.md with market snapshot table.

    Reads the snapshot metadata JSON file and updates the README
    with a formatted market table showing IST times and durations.
    """
    if not snapshot_file.exists():
        typer.echo(f"Error: snapshot file not found: {snapshot_file}", err=True)
        raise typer.Exit(code=1)

    if not readme.exists():
        typer.echo(f"Error: README not found: {readme}", err=True)
        raise typer.Exit(code=1)

    market_data = load_market_data_from_json(snapshot_file)
    modified = update_readme_snapshot(readme, market_data)

    if modified:
        typer.echo(f"Updated README.md with {len(market_data)} market snapshots")
    else:
        typer.echo("No changes needed to README.md")
