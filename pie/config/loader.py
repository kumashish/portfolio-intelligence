"""YAML configuration loading."""

from pathlib import Path
from typing import Any

import yaml

from pie.config.models import AppConfig


def load_config(path: Path) -> AppConfig:
    """Load and validate application configuration from a YAML file."""
    raw_config: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw_config is None:
        raw_config = {}
    if not isinstance(raw_config, dict):
        msg = "Configuration root must be a mapping."
        raise ValueError(msg)
    return AppConfig.model_validate(raw_config)
