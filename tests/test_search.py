from __future__ import annotations

import polars as pl
import pytest

from csv_dis.search import SearchHits, search_frame, split_terms


@pytest.fixture()
def frame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "name": ["Apfel", "Birne", "Äpfel", None, "a.b"],
            "ort": ["Berlin", "München", "Berlin", "Köln", "Hamburg"],
            "preis": ["1", "2", "3", "4", "5"],
        }
    )


def _rows(hits: SearchHits) -> list[int]:
    return [hits.row_at(index) for index in range(hits.count)]


def test_split_terms_ignores_whitespace() -> None:
    assert split_terms("  Apfel   Berlin ") == ("Apfel", "Berlin")
    assert split_terms("   ") == ()
    assert split_terms("") == ()


def test_single_term_is_case_insensitive_substring(
    frame: pl.DataFrame,
) -> None:
    hits = search_frame(frame, list(frame.columns), "BERLIN")
    assert _rows(hits) == [0, 2]
    assert hits.count == 2


def test_empty_search_has_no_hits(frame: pl.DataFrame) -> None:
    assert search_frame(frame, list(frame.columns), "").count == 0
    assert search_frame(frame, list(frame.columns), "   ").count == 0


def test_umlauts_are_not_folded(frame: pl.DataFrame) -> None:
    assert _rows(search_frame(frame, ["name"], "apfel")) == [0]
    assert _rows(search_frame(frame, ["name"], "äpfel")) == [2]


def test_sharp_s_matches_case_insensitively() -> None:
    frame = pl.DataFrame({"name": ["Straße", "Strasse"]})
    assert _rows(search_frame(frame, ["name"], "straße")) == [0]
    assert _rows(search_frame(frame, ["name"], "STRASSE")) == [1]


def test_all_terms_must_match_the_same_row(frame: pl.DataFrame) -> None:
    hits = search_frame(frame, ["name", "ort"], "apfel berlin")
    assert _rows(hits) == [0]

    assert search_frame(frame, ["name", "ort"], "birne berlin").count == 0


def test_cells_only_highlighted_in_matching_rows(
    frame: pl.DataFrame,
) -> None:
    hits = search_frame(frame, ["name", "ort"], "apfel berlin")
    assert hits.cell_hit(0, "name") is True
    assert hits.cell_hit(0, "ort") is True
    assert hits.cell_hit(1, "ort") is False


def test_hidden_columns_are_not_searched(frame: pl.DataFrame) -> None:
    assert search_frame(frame, ["name"], "berlin").count == 0


def test_empty_cells_do_not_match(frame: pl.DataFrame) -> None:
    hits = search_frame(frame, ["name", "ort"], "köln")
    assert _rows(hits) == [3]
    assert hits.cell_hit(3, "name") is False
    assert hits.cell_hit(3, "ort") is True


def test_special_characters_are_literal(frame: pl.DataFrame) -> None:
    assert _rows(search_frame(frame, ["name"], "a.b")) == [4]
    assert search_frame(frame, ["name"], "a?b").count == 0


def test_no_columns_and_empty_frame() -> None:
    frame = pl.DataFrame({"name": ["Apfel"]})
    assert search_frame(frame, [], "apfel").count == 0
    assert search_frame(frame.head(0), ["name"], "apfel").count == 0


def test_empty_hits_are_safe() -> None:
    hits = SearchHits()
    assert hits.count == 0
    assert hits.cell_hit(0, "name") is False
    assert hits.first_column(0, ["name"]) is None
