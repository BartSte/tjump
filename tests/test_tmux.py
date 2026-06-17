"""Tests for tmux command construction."""

from __future__ import annotations

from tjump import tmux


def test_launch_popup_covers_target_pane(monkeypatch) -> None:
    """The overlay popup should be positioned over the target pane."""

    commands: list[tuple[str, ...]] = []
    state = tmux.PaneState(
        pane_id="%1",
        cursor_x=0,
        cursor_y=0,
        pane_width=80,
        pane_height=24,
        lines=[],
    )

    monkeypatch.setattr(tmux, "read_pane_state", lambda pane_id: state)
    monkeypatch.setattr(tmux, "write_state", lambda state: "/tmp/tjump.json")
    monkeypatch.setattr(
        tmux, "tmux", lambda *args, **kwargs: commands.append(args)
    )

    tmux.launch_popup("%1")

    assert len(commands) == 1
    command = commands[0]
    assert command[:13] == (
        "display-popup",
        "-E",
        "-B",
        "-w",
        "80",
        "-h",
        "24",
        "-x",
        "#{popup_pane_left}",
        "-y",
        "#{popup_pane_top}",
        "-t",
        "%1",
    )
