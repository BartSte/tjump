"""Terminal popup UI for interactive tjump searches."""

from __future__ import annotations

import argparse
import os
import sys
import termios
import tty
from collections.abc import Iterator

from tjump import config as tjump_config
from tjump import search as tjump_search
from tjump import tmux


CSI = "\x1b["


def clipped_lines(state: tmux.PaneState) -> list[str]:
    """Returns visible content rows, excluding the popup status row."""

    return state.lines[: max(0, state.pane_height - 1)]


def label_map(matches: list[tjump_search.Match]) -> dict[str, tjump_search.Match]:
    """Maps assigned label keys to matches."""

    return {match.label: match for match in matches if match.label}


def iter_keypresses() -> Iterator[str]:
    """Yields raw keypresses from stdin.

    Yields:
      Single printable characters or escape-prefixed control sequences.
    """

    while True:
        char = sys.stdin.read(1)
        if not char:
            return
        if char == "\x1b":
            extra = ""
            while True:
                rlist, _, _ = __import__("select").select([sys.stdin], [], [], 0.01)
                if not rlist:
                    break
                extra += sys.stdin.read(1)
            yield char + extra
        else:
            yield char


def overlay_line(
    line: str,
    row: int,
    matches: list[tjump_search.Match],
    width: int,
    settings: tjump_config.Settings,
) -> str:
    """Renders one captured pane line with match highlights.

    Args:
      line: Original pane line.
      row: Zero-based row index.
      matches: Labelled matches.
      width: Pane width.
      settings: Rendering settings.

    Returns:
      The rendered terminal line.
    """

    line_matches = [
        match for match in matches if match.row == row and match.col < width
    ]
    if not line_matches:
        return line[:width]

    chunks: list[str] = []
    index = 0
    for match in line_matches:
        start = min(match.col, width)
        end = min(match.col + max(len(match.text), 1), width)
        if start < index:
            continue
        chunks.append(line[index:start])
        visible = line[start:end]
        if match.label and visible:
            chunks.append(f"\x1b[{settings.label_style}m{match.label}\x1b[0m")
            if len(visible) > 1:
                chunks.append(f"\x1b[{settings.match_style}m{visible[1:]}\x1b[0m")
        elif visible:
            chunks.append(f"\x1b[{settings.match_style}m{visible}\x1b[0m")
        index = end
    chunks.append(line[index:width])
    return "".join(chunks)


def render(
    state: tmux.PaneState,
    query: str,
    matches: list[tjump_search.Match],
    settings: tjump_config.Settings,
) -> None:
    """Renders the complete popup overlay."""

    width = state.pane_width
    height = state.pane_height
    body_height = max(0, height - 1)
    out = [f"{CSI}?25l", f"{CSI}H"]

    lines = clipped_lines(state)
    for row in range(body_height):
        line = lines[row] if row < len(lines) else ""
        rendered = overlay_line(line, row, matches, width, settings)
        out.append(rendered)
        out.append(f"{CSI}K")
        if row < body_height - 1:
            out.append("\r\n")

    status = f"{settings.prompt}: {query}"
    if query and settings.show_match_count:
        status += f"  [{len(matches)}]"
    out.append(
        f"\r\n{CSI}{settings.status_style}m{status[:width]:<{width}}\x1b[0m"
    )
    sys.stdout.write("".join(out))
    sys.stdout.flush()


def choose_match(state: tmux.PaneState, match: tjump_search.Match) -> None:
    """Moves the copy-mode cursor to a selected match."""

    tmux.move_copy_cursor(
        state.pane_id,
        state.cursor_x,
        state.cursor_y,
        match.col,
        match.row,
    )


def run_popup(state_path: str, config: str | None = None) -> int:
    """Runs the popup UI against captured pane state.

    Args:
      state_path: Path to the temporary pane state JSON file.
      config: Optional config file path.

    Returns:
      A process exit code.
    """

    try:
        state = tmux.load_state(state_path)
        settings = tjump_config.load_settings(config)
        query = ""
        matches: list[tjump_search.Match] = []
        old_attrs = termios.tcgetattr(sys.stdin)

        try:
            tty.setraw(sys.stdin.fileno())
            render(state, query, matches, settings)
            for key in iter_keypresses():
                labels = label_map(matches)
                if key in ("\x03", "\x1b"):
                    return 130
                if key in ("\r", "\n"):
                    if matches:
                        choose_match(state, matches[0])
                        return 0
                    continue
                if key in ("\x7f", "\b"):
                    query = query[:-1]
                elif len(key) == 1 and key in labels:
                    choose_match(state, labels[key])
                    return 0
                elif len(key) == 1 and key.isprintable():
                    query += key
                else:
                    continue
                matches = tjump_search.search(
                    clipped_lines(state),
                    query,
                    settings.label_alphabet,
                )
                render(state, query, matches, settings)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_attrs)
            sys.stdout.write(f"{CSI}?25h\x1b[0m")
            sys.stdout.flush()
    finally:
        try:
            os.unlink(state_path)
        except FileNotFoundError:
            pass

    return 0


def main(argv: list[str] | None = None) -> int:
    """Runs the tjump command-line interface."""

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--pane", default=os.environ.get("TMUX_PANE"))
    parser.add_argument("--popup")
    parser.add_argument("--config", help="path to a tjump TOML config file")
    args = parser.parse_args(argv)

    if args.popup:
        return run_popup(args.popup, args.config)
    if not args.pane:
        parser.error("missing target pane")
    tmux.launch_popup(args.pane, args.config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
