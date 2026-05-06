# tjump

`tjump` is a small dependency-free Python tool for jumping to visible text in
tmux copy-mode.

It provides one focused flow:

1. Enter tmux copy-mode.
2. Press `h`.
3. Type a literal text query.
4. Pick a highlighted label, or press `Enter` for the first labelled match.
5. Stay in copy-mode with the cursor moved to the start of the match.

It does not select, yank, paste, or leave copy-mode.

## Requirements

- `tmux`
- `python3`
- `uv`

## Installation

Clone the repo somewhere stable, then source `tjump.tmux` from your tmux config:

```tmux
source-file ~/code/personal/tjump/tjump.tmux
```

Reload tmux:

```sh
tmux source-file ~/.tmux.conf
```

The provided tmux plugin file binds `h` in the `copy-mode-vi` key table:

```tmux
bind -T copy-mode-vi h run-shell -b "$HOME/code/personal/tjump/bin/tjump --pane '#{pane_id}'"
```

If the repo lives somewhere else, update that path in `tjump.tmux`.

Install the development environment with:

```sh
uv sync
```

## Usage

Enter copy-mode, then press `h`.

Type the text you want to jump to. Matches are highlighted in the visible pane
content, and each labelled match gets a one-character label. Press a label to
move the copy-mode cursor to that match.

Keys inside the popup:

| Key | Action |
| --- | --- |
| Printable character | Extend the query |
| `Backspace` | Delete the last query character |
| Label key | Jump to that labelled match |
| `Enter` | Jump to the first labelled match |
| `Esc` | Cancel |
| `Ctrl-c` | Cancel |

## Search Behavior

- Searches only the currently visible tmux copy-mode pane content.
- Matches literal substrings, not regular expressions.
- Preserves repeated and overlapping matches on the same line.
- Uses smartcase:
  - all-lowercase queries search case-insensitively;
  - queries with any uppercase character search case-sensitively.
- Assigns labels top-to-bottom, left-to-right.
- Uses this label alphabet:

```text
tnseriaogmplfuwyqbjdhvkzxc
```

Labels that conflict with possible query continuation characters are skipped.
For example, if the current query is `the` and a match is followed by `r`, the
label `r` is avoided so typing can continue to `ther` instead of immediately
choosing a label.

## CLI

```sh
bin/tjump --pane '#{pane_id}'
```

After `uv sync`, the packaged console command is also available through:

```sh
uv run tjump --pane '#{pane_id}'
```

Options:

```text
-h, --help       show help
-p, --pane PANE  target tmux pane
--popup POPUP    internal popup state file
```

Normal use should go through the tmux binding. `--popup` is an internal mode
used after `tjump` captures pane state and launches the full-pane popup.

## Development

Run the checks from this repo:

```sh
uv run pytest
uv run python -m compileall src/tjump
bin/tjump --help
```

Check tmux wiring with:

```sh
tmux source-file ~/.tmux.conf
tmux list-keys -T copy-mode-vi h
```

Useful manual checks:

- `h -> query -> label` lands the cursor on the match start.
- `h -> query -> Enter` lands on the first labelled match.
- `h -> query -> Backspace` updates matches.
- `Esc` and `Ctrl-c` cancel without moving.
- `v -> h -> query -> label -> y` still yanks the selected text.

## Layout

```text
bin/tjump            executable entrypoint used by the tmux binding
src/tjump/search.py  literal search, smartcase, and label assignment
src/tjump/ui.py      popup UI, incremental input, rendering, and key handling
src/tjump/tmux.py    tmux capture, popup launch, and copy cursor movement
tjump.tmux          tmux loader and copy-mode binding
tests/              unit tests for search behavior
```
