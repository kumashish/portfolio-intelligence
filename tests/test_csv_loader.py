from pathlib import Path

import pytest

from pie.market_data.csv_loader import load_ohlcv_csv


def test_load_ohlcv_csv_normalizes_source_columns(tmp_path: Path) -> None:
    csv_path = tmp_path / "nifty.csv"
    csv_path.write_text(
        "Date,Open,High,Low,Close,Volume\n2026-01-01,100,110,90,105,1000\n",
        encoding="utf-8",
    )

    data = load_ohlcv_csv(csv_path)

    assert data.columns == ["timestamp", "open", "high", "low", "close", "volume"]
    assert data.get_column("close").item() == 105.0


def test_load_ohlcv_csv_rejects_missing_columns(tmp_path: Path) -> None:
    csv_path = tmp_path / "incomplete.csv"
    csv_path.write_text("Date,Close\n2026-01-01,105\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required columns"):
        load_ohlcv_csv(csv_path)
