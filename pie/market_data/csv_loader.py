"""Loading of canonical OHLCV data from local CSV files."""

from pathlib import Path

import polars as pl

REQUIRED_SOURCE_COLUMNS = {"Date", "Open", "High", "Low", "Close", "Volume"}


def load_ohlcv_csv(path: Path) -> pl.DataFrame:
    """Load a Date/Open/High/Low/Close/Volume CSV into canonical OHLCV columns."""
    data = pl.read_csv(path)
    missing_columns = REQUIRED_SOURCE_COLUMNS.difference(data.columns)
    if missing_columns:
        msg = f"CSV is missing required columns: {sorted(missing_columns)}"
        raise ValueError(msg)
    return data.select(
        pl.col("Date").str.strptime(pl.Datetime, format="%Y-%m-%d", strict=True).alias("timestamp"),
        pl.col("Open").cast(pl.Float64, strict=True).alias("open"),
        pl.col("High").cast(pl.Float64, strict=True).alias("high"),
        pl.col("Low").cast(pl.Float64, strict=True).alias("low"),
        pl.col("Close").cast(pl.Float64, strict=True).alias("close"),
        pl.col("Volume").cast(pl.Int64, strict=True).alias("volume"),
    )
