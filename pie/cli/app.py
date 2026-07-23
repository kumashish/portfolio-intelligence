"""Typer command-line interface."""

from pathlib import Path

import typer
from rich.console import Console

from pie.config.loader import load_config

app = typer.Typer(help="Portfolio Intelligence Engine.", no_args_is_help=True)
console = Console()


@app.command("analyze-market")
def analyze_market(symbol: str) -> None:
    """Placeholder command for analyzing market data for a symbol."""
    console.print(f"Market analysis for {symbol} is not implemented yet.")


@app.command()
def portfolio(account_id: str) -> None:
    """Placeholder command for inspecting a portfolio."""
    console.print(f"Portfolio inspection for {account_id} is not implemented yet.")


@app.command()
def recommend(account_id: str) -> None:
    """Placeholder command for producing a recommendation."""
    console.print(f"Recommendation generation for {account_id} is not implemented yet.")


@app.command("config-check")
def config_check(path: Path) -> None:
    """Validate a configuration file."""
    load_config(path)
    console.print(f"Configuration is valid: {path}")


def main() -> None:
    """Run the CLI application."""
    app()
