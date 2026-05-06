"""Configuration loading and validation for tjump."""

from __future__ import annotations

import dataclasses
import os
import pathlib
from typing import Any

from tjump import search

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


CONFIG_ENV = "TJUMP_CONFIG"
DEFAULT_CONFIG_FILE = "config.toml"


@dataclasses.dataclass(frozen=True)
class Settings:
    """User-configurable settings for search labels and popup rendering."""

    label_alphabet: str = search.LABEL_ALPHABET
    prompt: str = "tjump"
    show_match_count: bool = True
    label_style: str = "1;30;42"
    match_style: str = "30;43"
    status_style: str = "7"


def default_config_path() -> pathlib.Path:
    """Returns the default user config path."""

    config_home = os.environ.get("XDG_CONFIG_HOME")
    if config_home:
        return pathlib.Path(config_home) / "tjump" / DEFAULT_CONFIG_FILE
    return pathlib.Path.home() / ".config" / "tjump" / DEFAULT_CONFIG_FILE


def config_path(path: str | None = None) -> pathlib.Path:
    """Resolves the config path from an argument, environment, or default.

    Args:
      path: Optional explicit path passed on the command line.

    Returns:
      The expanded config file path.
    """

    if path:
        return pathlib.Path(path).expanduser()
    env_path = os.environ.get(CONFIG_ENV)
    if env_path:
        return pathlib.Path(env_path).expanduser()
    return default_config_path()


def load_settings(path: str | None = None) -> Settings:
    """Loads settings from a TOML config file.

    Args:
      path: Optional explicit config path.

    Returns:
      Parsed settings, or defaults when the config file does not exist.

    Raises:
      ValueError: If the config file contains invalid settings.
      tomllib.TOMLDecodeError: If the config file is not valid TOML.
    """

    resolved = config_path(path)
    if not resolved.exists():
        return Settings()

    with resolved.open("rb") as handle:
        data = tomllib.load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"{resolved}: config must be a TOML table")
    return settings_from_table(data, resolved)


def settings_from_table(
    data: dict[str, Any],
    source: pathlib.Path | None = None,
) -> Settings:
    """Builds settings from a parsed TOML table.

    Args:
      data: Parsed TOML table.
      source: Optional source path for error messages.

    Returns:
      Validated settings.

    Raises:
      ValueError: If any key or value is invalid.
    """

    allowed = {field.name for field in dataclasses.fields(Settings)}
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ValueError(
            f"{format_source(source)}unknown setting: {', '.join(unknown)}"
        )

    settings = Settings()
    values: dict[str, Any] = {}
    for name in allowed:
        if name in data:
            values[name] = validate_setting(name, data[name], settings)

    return Settings(**values)


def validate_setting(name: str, value: Any, defaults: Settings) -> Any:
    """Validates one setting value.

    Args:
      name: Setting name.
      value: Setting value from TOML.
      defaults: Default settings used for unknown internal fallbacks.

    Returns:
      A validated setting value.

    Raises:
      ValueError: If the value is invalid for the setting.
    """

    if name in {"label_alphabet", "prompt"}:
        if not isinstance(value, str):
            raise ValueError(f"{name} must be a string")
        if name == "label_alphabet":
            return validate_label_alphabet(value)
        if not value:
            raise ValueError("prompt must not be empty")
        return value

    if name == "show_match_count":
        if not isinstance(value, bool):
            raise ValueError("show_match_count must be true or false")
        return value

    if name in {"label_style", "match_style", "status_style"}:
        if not isinstance(value, str):
            raise ValueError(f"{name} must be a string")
        return validate_sgr_style(name, value)

    return getattr(defaults, name)


def validate_label_alphabet(value: str) -> str:
    """Validates the label alphabet.

    Args:
      value: Candidate label alphabet.

    Returns:
      The validated label alphabet.

    Raises:
      ValueError: If the alphabet is empty, duplicated, or not key-safe.
    """

    if not value:
        raise ValueError("label_alphabet must not be empty")
    if any(len(char.encode("utf-8")) != 1 for char in value):
        raise ValueError("label_alphabet must contain only single-byte characters")
    if any(not char.isprintable() or char.isspace() for char in value):
        raise ValueError(
            "label_alphabet must contain only printable non-space characters"
        )
    if len(set(value)) != len(value):
        raise ValueError("label_alphabet must not contain duplicate characters")
    return value


def validate_sgr_style(name: str, value: str) -> str:
    """Validates a semicolon-separated ANSI SGR style.

    Args:
      name: Setting name used in errors.
      value: Candidate SGR style.

    Returns:
      The validated SGR style.

    Raises:
      ValueError: If the style contains unsupported tokens.
    """

    if not value:
        raise ValueError(f"{name} must not be empty")
    parts = value.split(";")
    for part in parts:
        if not part.isdigit():
            raise ValueError(f"{name} must be semicolon-separated ANSI SGR numbers")
        number = int(part)
        if number < 0 or number > 107:
            raise ValueError(f"{name} contains unsupported ANSI SGR number: {number}")
    return value


def format_source(source: pathlib.Path | None) -> str:
    """Formats a config source prefix for error messages."""

    return f"{source}: " if source else ""
