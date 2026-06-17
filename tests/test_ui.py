"""Tests for popup UI control flow."""

from __future__ import annotations

import pytest

from tjump import config
from tjump import tmux
from tjump import ui


class FakeStdin:
    """Minimal stdin object for terminal setup calls."""

    def fileno(self) -> int:
        """Returns a harmless file descriptor number."""

        return 0


@pytest.mark.parametrize("key", ["\x1b", "\x03"])
def test_cancel_exits_successfully_without_moving_cursor(
    monkeypatch: pytest.MonkeyPatch,
    key: str,
) -> None:
    """Cancel keys should close the popup without tmux reporting an error."""

    state = tmux.PaneState(
        pane_id="%1",
        cursor_x=0,
        cursor_y=0,
        pane_width=80,
        pane_height=24,
        lines=["needle"],
    )
    moved = False

    def choose_match(
        state: tmux.PaneState,
        match,
    ) -> None:
        nonlocal moved
        moved = True

    monkeypatch.setattr(ui.tmux, "load_state", lambda path: state)
    monkeypatch.setattr(
        ui.tjump_config, "load_settings", lambda path: config.Settings()
    )
    monkeypatch.setattr(ui.termios, "tcgetattr", lambda stream: [])
    monkeypatch.setattr(
        ui.termios, "tcsetattr", lambda stream, when, attrs: None
    )
    monkeypatch.setattr(ui.tty, "setraw", lambda fd: None)
    monkeypatch.setattr(ui.sys, "stdin", FakeStdin())
    monkeypatch.setattr(
        ui, "render", lambda state, query, matches, settings: None
    )
    monkeypatch.setattr(ui, "iter_keypresses", lambda: iter([key]))
    monkeypatch.setattr(ui, "choose_match", choose_match)

    assert ui.run_popup("/tmp/tjump-missing.json") == 0
    assert not moved
