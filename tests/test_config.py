"""Tests for tjump configuration loading."""

from __future__ import annotations

import pathlib

import pytest

from tjump import config


def test_missing_config_uses_defaults(tmp_path: pathlib.Path) -> None:
    """Missing config files should not change defaults."""

    settings = config.load_settings(str(tmp_path / "missing.toml"))

    assert settings == config.Settings()


def test_config_file_can_override_common_settings(tmp_path: pathlib.Path) -> None:
    """A TOML config file should override user-facing settings."""

    path = tmp_path / "config.toml"
    path.write_text(
        "\n".join(
            [
                'label_alphabet = "abc"',
                'prompt = "jump"',
                "show_match_count = false",
                'label_style = "1;37;44"',
                'match_style = "30;47"',
                'status_style = "7;32"',
            ]
        ),
        encoding="utf-8",
    )

    settings = config.load_settings(str(path))

    assert settings.label_alphabet == "abc"
    assert settings.prompt == "jump"
    assert not settings.show_match_count
    assert settings.label_style == "1;37;44"
    assert settings.match_style == "30;47"
    assert settings.status_style == "7;32"


def test_config_rejects_unknown_settings() -> None:
    """Unknown config keys should fail loudly."""

    with pytest.raises(ValueError, match="unknown setting"):
        config.settings_from_table({"nope": True})


def test_config_rejects_duplicate_label_alphabet() -> None:
    """Duplicate labels would make match selection ambiguous."""

    with pytest.raises(ValueError, match="duplicate"):
        config.settings_from_table({"label_alphabet": "aa"})


def test_config_rejects_invalid_sgr_style() -> None:
    """ANSI styles must be numeric SGR sequences."""

    with pytest.raises(ValueError, match="ANSI SGR"):
        config.settings_from_table({"label_style": "bold"})
