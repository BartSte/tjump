from __future__ import annotations

from dataclasses import dataclass


LABEL_ALPHABET = "tnseriaogmplfuwyqbjdhvkzxc"


@dataclass(frozen=True)
class Match:
    row: int
    col: int
    text: str
    label: str | None = None


def is_case_sensitive(query: str) -> bool:
    return any(char.isupper() for char in query)


def find_literal_matches(lines: list[str], query: str) -> list[Match]:
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
    conflicts = label_conflicts(lines, matches, query)
    available = [label for label in alphabet if label not in conflicts]
    labelled: list[Match] = []

    for match, label in zip(matches, available):
        labelled.append(Match(row=match.row, col=match.col, text=match.text, label=label))

    return labelled


def search(lines: list[str], query: str, alphabet: str = LABEL_ALPHABET) -> list[Match]:
    return assign_labels(lines, find_literal_matches(lines, query), query, alphabet)

