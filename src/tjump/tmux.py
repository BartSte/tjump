"""tmux integration for pane capture, popup launch, and cursor movement."""

from __future__ import annotations

import dataclasses
import json
import os
import pathlib
import shlex
import subprocess
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[2]


@dataclasses.dataclass(frozen=True)
class PaneState:
    """Captured tmux copy-mode pane state used by the popup."""

    pane_id: str
    cursor_x: int
    cursor_y: int
    pane_width: int
    pane_height: int
    lines: list[str]


def tmux(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Runs a tmux command.

    Args:
      *args: tmux command arguments.
      check: Whether subprocess should raise on a non-zero exit.

    Returns:
      The completed tmux process.
    """

    return subprocess.run(
        ["tmux", *args],
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def display_format(pane_id: str, fmt: str) -> str:
    """Reads a tmux format string for a pane."""

    return tmux("display-message", "-p", "-t", pane_id, fmt).stdout.strip()


def capture_visible_lines(pane_id: str) -> list[str]:
    """Captures the visible copy-mode pane content."""

    output = tmux("capture-pane", "-p", "-M", "-N", "-t", pane_id).stdout
    return output.splitlines()


def read_pane_state(pane_id: str) -> PaneState:
    """Reads cursor, size, and visible content for a pane."""

    fmt = "#{copy_cursor_x}\t#{copy_cursor_y}\t#{pane_width}\t#{pane_height}"
    raw = display_format(pane_id, fmt)
    cursor_x, cursor_y, pane_width, pane_height = (
        int(value) for value in raw.split("\t")
    )
    return PaneState(
        pane_id=pane_id,
        cursor_x=cursor_x,
        cursor_y=cursor_y,
        pane_width=pane_width,
        pane_height=pane_height,
        lines=capture_visible_lines(pane_id),
    )


def write_state(state: PaneState) -> str:
    """Writes popup state to a temporary JSON file."""

    fd, path = tempfile.mkstemp(prefix="tjump-", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(dataclasses.asdict(state), handle)
    return path


def load_state(path: str) -> PaneState:
    """Loads popup state from a temporary JSON file."""

    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return PaneState(**data)


def launch_popup(pane_id: str, config: str | None = None) -> None:
    """Launches the full-pane tmux popup.

    Args:
      pane_id: Target tmux pane id.
      config: Optional config file path to pass to the popup process.
    """

    state_path = write_state(read_pane_state(pane_id))
    src = ROOT / "src"
    python = shlex.quote(sys.executable)
    popup = shlex.quote(state_path)
    config_arg = f" --config {shlex.quote(config)}" if config else ""
    if src.is_dir():
        pythonpath = shlex.quote(str(src))
        command = (
            f"PYTHONPATH={pythonpath}${{PYTHONPATH:+:$PYTHONPATH}} "
            f"{python} -m tjump.ui --popup {popup}{config_arg}"
        )
    else:
        command = f"{python} -m tjump.ui --popup {popup}{config_arg}"
    tmux(
        "display-popup",
        "-E",
        "-B",
        "-w",
        "100%",
        "-h",
        "100%",
        "-t",
        pane_id,
        command,
    )


def move_copy_cursor(
    pane_id: str,
    from_x: int,
    from_y: int,
    to_x: int,
    to_y: int,
) -> None:
    """Moves the tmux copy-mode cursor by relative cursor commands.

    Args:
      pane_id: Target tmux pane id.
      from_x: Current cursor column.
      from_y: Current cursor row.
      to_x: Target cursor column.
      to_y: Target cursor row.
    """

    dy = to_y - from_y
    dx = to_x - from_x

    if dy:
        command = "cursor-down" if dy > 0 else "cursor-up"
        tmux("send-keys", "-t", pane_id, "-N", str(abs(dy)), "-X", command)

    if dx:
        command = "cursor-right" if dx > 0 else "cursor-left"
        tmux("send-keys", "-t", pane_id, "-N", str(abs(dx)), "-X", command)
