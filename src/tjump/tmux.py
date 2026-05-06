from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class PaneState:
    pane_id: str
    cursor_x: int
    cursor_y: int
    pane_width: int
    pane_height: int
    lines: list[str]


def tmux(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["tmux", *args],
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def display_format(pane_id: str, fmt: str) -> str:
    return tmux("display-message", "-p", "-t", pane_id, fmt).stdout.strip()


def capture_visible_lines(pane_id: str) -> list[str]:
    output = tmux("capture-pane", "-p", "-M", "-N", "-t", pane_id).stdout
    return output.splitlines()


def read_pane_state(pane_id: str) -> PaneState:
    fmt = "#{copy_cursor_x}\t#{copy_cursor_y}\t#{pane_width}\t#{pane_height}"
    raw = display_format(pane_id, fmt)
    cursor_x, cursor_y, pane_width, pane_height = (int(value) for value in raw.split("\t"))
    return PaneState(
        pane_id=pane_id,
        cursor_x=cursor_x,
        cursor_y=cursor_y,
        pane_width=pane_width,
        pane_height=pane_height,
        lines=capture_visible_lines(pane_id),
    )


def write_state(state: PaneState) -> str:
    fd, path = tempfile.mkstemp(prefix="tjump-", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(asdict(state), handle)
    return path


def load_state(path: str) -> PaneState:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return PaneState(**data)


def launch_popup(pane_id: str) -> None:
    state_path = write_state(read_pane_state(pane_id))
    src = ROOT / "src"
    python = shlex.quote(sys.executable)
    popup = shlex.quote(state_path)
    if src.is_dir():
        pythonpath = shlex.quote(str(src))
        command = f"PYTHONPATH={pythonpath}${{PYTHONPATH:+:$PYTHONPATH}} {python} -m tjump.ui --popup {popup}"
    else:
        command = f"{python} -m tjump.ui --popup {popup}"
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


def move_copy_cursor(pane_id: str, from_x: int, from_y: int, to_x: int, to_y: int) -> None:
    dy = to_y - from_y
    dx = to_x - from_x

    if dy:
        command = "cursor-down" if dy > 0 else "cursor-up"
        tmux("send-keys", "-t", pane_id, "-N", str(abs(dy)), "-X", command)

    if dx:
        command = "cursor-right" if dx > 0 else "cursor-left"
        tmux("send-keys", "-t", pane_id, "-N", str(abs(dx)), "-X", command)
