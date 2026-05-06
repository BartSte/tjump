from tjump.search import find_literal_matches, label_conflicts, search


def positions(matches):
    return [(match.row, match.col) for match in matches]


def labels(matches):
    return [match.label for match in matches]


def test_literal_substring_search_matches_punctuation():
    matches = find_literal_matches(["foo.* bar foo.*"], "foo.*")

    assert positions(matches) == [(0, 0), (0, 10)]


def test_lowercase_query_is_case_insensitive():
    matches = find_literal_matches(["Alpha alpha ALPHA"], "alpha")

    assert positions(matches) == [(0, 0), (0, 6), (0, 12)]


def test_uppercase_query_is_case_sensitive():
    matches = find_literal_matches(["Alpha alpha ALPHA"], "Al")

    assert positions(matches) == [(0, 0)]


def test_repeated_matches_on_one_line_overlap():
    matches = find_literal_matches(["aaaa"], "aa")

    assert positions(matches) == [(0, 0), (0, 1), (0, 2)]


def test_label_conflicts_avoid_possible_query_continuations():
    lines = ["theta there then"]
    matches = find_literal_matches(lines, "the")

    assert label_conflicts(lines, matches, "the") == {"t", "r", "n"}
    assert labels(search(lines, "the"))[:3] == ["s", "e", "i"]


def test_enter_first_match_ordering_is_top_to_bottom_then_left_to_right():
    matches = search(["xx needle", "needle later"], "needle")

    assert positions(matches) == [(0, 3), (1, 0)]
    assert matches[0].label == "t"

