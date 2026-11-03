"""Configuration loader for Payal."""

import json
from pathlib import Path

from .config import CONFIG, PayalConfig
from .identity import get_identity
from .persona import DEFAULT_PERSONA, SYSTEM_PROMPT


def load_identity():
    return get_identity()


def load_persona():
    return DEFAULT_PERSONA


def load_config(config_path: Path | None = None) -> PayalConfig:
    """Load configuration, optionally from a JSON file."""

    if config_path is None:
        return CONFIG

    config_path = Path(config_path).resolve()

    if not config_path.is_file():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}"
        )

    with config_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return PayalConfig.model_validate(data)


def get_system_prompt() -> str:
    return SYSTEM_PROMPT

