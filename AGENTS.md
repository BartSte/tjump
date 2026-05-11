# AGENTS.md

## Project Context

`tjump` is a small dependency-free Python tool for jumping inside tmux copy-mode.
It is intended to replace the old tmux easy-motion wiring for one focused flow:

1. Enter tmux copy-mode.
2. Press `h`.
3. Type a literal visible-text query.
4. Pick a highlighted label, or press `Enter` for the first labelled match.
5. Move the copy-mode cursor to the match start without selecting, yanking, pasting,
   or leaving copy-mode.

The tool should behave like the user's `nvim-jump` workflow where practical.

## Repository Layout

- `src/tjump/search.py`: literal substring search, smartcase, and label assignment.
- `src/tjump/ui.py`: full-pane popup UI, incremental input, highlighting, labels,
  backspace, enter, and cancel handling.
- `src/tjump/tmux.py`: tmux capture, pane state, popup launch, and copy cursor movement.
- The tmux binding is documented in `README.md` instead of shipped as a loader file.
- `tests/`: focused unit tests for search behavior.

Dotfiles wiring lives outside this repo. `~/.tmux.conf` should source the user's
dotfiles jump config, not `easy-motion.conf`.

## Behavior Requirements

- Search only the currently visible tmux copy-mode pane content.
- Search arbitrary literal substrings, not regexes and not only words.
- Use smartcase:
  - all-lowercase query searches case-insensitively;
  - any uppercase query character makes the search case-sensitive.
- Preserve repeated and overlapping matches on the same line.
- Assign labels top-to-bottom, left-to-right using:
  `tnseriaogmplfuwyqbjdhvkzxc`
- Avoid label characters that could also be the next character after a current
  match, so typing can continue the query instead of immediately choosing a label.
- `Backspace` edits the query.
- `Enter` jumps to the first labelled match.
- `Esc` and `Ctrl-c` cancel without moving.
- Choosing a label moves only the tmux copy-mode cursor.
- Existing copy-mode bindings such as `v`, `C-v`, and `y` must remain unchanged.

## Implementation Notes

- Keep the project dependency-free unless there is a clear reason to add one.
- Prefer small, direct functions over framework-style abstractions.
- The tmux popup is intentionally full-pane and borderless so it overlays the
  visible copy-mode content.
- Cursor movement is done with `tmux send-keys -X cursor-*`; do not exit copy-mode.
- Be careful with symlinks when editing `~/.tmux.conf`; it points at the dotfiles
  copy under `~/dotfiles-linux/home/.tmux.conf`.

## Verification

Run from this repo:

```sh
uv run pytest
uv run python -m compileall src/tjump
uv run tjump --help
```

For tmux wiring:

```sh
tmux source-file ~/.tmux.conf
tmux list-keys -T copy-mode-vi h
```

Manual checks should include:

- `h -> query -> label` lands the cursor on the match start.
- `h -> query -> Enter` lands on the first labelled match.
- `h -> query -> Backspace` updates matches.
- `Esc` and `Ctrl-c` cancel without moving.
- `v -> h -> query -> label -> y` still yanks the selected text.
