"""CLI commands for updating the README market snapshot.

reports/market/snapshot.json is maintained incrementally: every
`pie analyze-market <SYMBOL>` run upserts its own row into that file
(see pie.reporting.snapshot.upsert_snapshot_entry). This module just
renders that file into the README table.
"""

from pathlib import Path
from typing import Annotated

import typer

from pie.reporting.readme_update import load_market_data_from_json, update_readme_snapshot

readme_app = typer.Typer(help="README update commands.", no_args_is_help=True)


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
