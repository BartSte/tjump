"""Tests for literal search and label assignment."""

from __future__ import annotations

from tjump import search as tjump_search


def positions(matches: list[tjump_search.Match]) -> list[tuple[int, int]]:
    """Returns row and column pairs for matches."""

    return [(match.row, match.col) for match in matches]


def labels(matches: list[tjump_search.Match]) -> list[str | None]:
    """Returns labels for matches."""

    return [match.label for match in matches]


def test_literal_substring_search_matches_punctuation() -> None:
    """Literal search should treat punctuation as ordinary text."""

    matches = tjump_search.find_literal_matches(["foo.* bar foo.*"], "foo.*")

    assert positions(matches) == [(0, 0), (0, 10)]


def test_lowercase_query_is_case_insensitive() -> None:
    """Lowercase queries should match text case-insensitively."""

    matches = tjump_search.find_literal_matches(["Alpha alpha ALPHA"], "alpha")

    assert positions(matches) == [(0, 0), (0, 6), (0, 12)]


def test_uppercase_query_is_case_sensitive() -> None:
    """Queries with uppercase characters should be case-sensitive."""

    matches = tjump_search.find_literal_matches(["Alpha alpha ALPHA"], "Al")

    assert positions(matches) == [(0, 0)]


def test_repeated_matches_on_one_line_overlap() -> None:
    """Overlapping matches should be preserved."""

    matches = tjump_search.find_literal_matches(["aaaa"], "aa")

    assert positions(matches) == [(0, 0), (0, 1), (0, 2)]


def test_label_conflicts_avoid_possible_query_continuations() -> None:
    """Label assignment should avoid possible continuation characters."""

    lines = ["theta there then"]
    matches = tjump_search.find_literal_matches(lines, "the")

    assert tjump_search.label_conflicts(lines, matches, "the") == {"t", "r", "n"}
    assert labels(tjump_search.search(lines, "the"))[:3] == ["s", "e", "i"]


def test_enter_first_match_ordering_is_top_to_bottom_then_left_to_right() -> None:
    """The first labelled match should be top-to-bottom, then left-to-right."""

    matches = tjump_search.search(["xx needle", "needle later"], "needle")

    assert positions(matches) == [(0, 3), (1, 0)]
    assert matches[0].label == "t"
