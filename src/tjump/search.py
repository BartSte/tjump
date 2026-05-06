"""Literal search and label assignment for tmux copy-mode content."""

from __future__ import annotations

import dataclasses


LABEL_ALPHABET = "tnseriaogmplfuwyqbjdhvkzxc"


@dataclasses.dataclass(frozen=True)
class Match:
    """A visible text match in captured tmux pane content."""

    row: int
    col: int
    text: str
    label: str | None = None


def is_case_sensitive(query: str) -> bool:
    """Returns whether query should use case-sensitive matching."""

    return any(char.isupper() for char in query)


def find_literal_matches(lines: list[str], query: str) -> list[Match]:
    """Finds literal substring matches in top-to-bottom display order.

    Args:
      lines: Visible pane lines.
      query: Literal query string.

    Returns:
      Matches in row-major order. Overlapping matches are preserved.
    """

    if not query:
        return []

    case_sensitive = is_case_sensitive(query)
    needle = query if case_sensitive else query.lower()
    matches: list[Match] = []

    for row, line in enumerate(lines):
        haystack = line if case_sensitive else line.lower()
        start = 0
        while True:
            col = haystack.find(needle, start)
            if col == -1:
                break
            matches.append(Match(row=row, col=col, text=line[col : col + len(query)]))
            start = col + 1

    return matches


def label_conflicts(lines: list[str], matches: list[Match], query: str) -> set[str]:
    """Finds label characters that would conflict with query continuation.

    Args:
      lines: Visible pane lines.
      matches: Current query matches.
      query: Literal query string.

    Returns:
      Label characters to avoid for the current query.
    """

    case_sensitive = is_case_sensitive(query)
    conflicts: set[str] = set()
    offset = len(query)

    for match in matches:
        line = lines[match.row]
        next_col = match.col + offset
        if next_col >= len(line):
            continue
        char = line[next_col]
        if char:
            conflicts.add(char if case_sensitive else char.lower())

    return conflicts


def assign_labels(
    lines: list[str],
    matches: list[Match],
    query: str,
    alphabet: str = LABEL_ALPHABET,
) -> list[Match]:
    """Assigns non-conflicting labels to matches.

    Args:
      lines: Visible pane lines.
      matches: Current query matches.
      query: Literal query string.
      alphabet: Candidate label characters in assignment order.

    Returns:
      Labelled matches, truncated when labels run out.
    """

    conflicts = label_conflicts(lines, matches, query)
    available = [label for label in alphabet if label not in conflicts]
    labelled: list[Match] = []

    for match, label in zip(matches, available):
        labelled.append(
            Match(row=match.row, col=match.col, text=match.text, label=label)
        )

    return labelled


def search(lines: list[str], query: str, alphabet: str = LABEL_ALPHABET) -> list[Match]:
    """Finds matches and assigns jump labels.

    Args:
      lines: Visible pane lines.
      query: Literal query string.
      alphabet: Candidate label characters in assignment order.

    Returns:
      Labelled matches in jump order.
    """

    return assign_labels(lines, find_literal_matches(lines, query), query, alphabet)
