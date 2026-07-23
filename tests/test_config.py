from pathlib import Path

import pytest
from pydantic import ValidationError

from pie.config.loader import load_config


def test_load_config_validates_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "logging:\n  level: DEBUG\nproviders:\n  demo:\n    enabled: false\n",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.logging.level == "DEBUG"
    assert config.providers["demo"].enabled is False


def test_load_config_rejects_unknown_values(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("unknown: true\n", encoding="utf-8")

    with pytest.raises(ValidationError):
        load_config(config_path)


def test_load_config_accepts_indicator_configuration(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("indicators:\n  - ema:\n      period: 20\n", encoding="utf-8")

    config = load_config(config_path)

    assert config.indicators == [{"ema": {"period": 20}}]
