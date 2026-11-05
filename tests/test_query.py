from __future__ import annotations

import polars as pl
import pytest

from csv_dis.column_types import ColumnType
from csv_dis.query import (
    Filter,
    FilterOperator,
    QueryError,
    SortSpec,
    apply_query,
    build_filter_expr,
    parse_date,
    parse_number,
)


@pytest.fixture()
def frame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "name": ["Apfel", "birne", "Äpfel", None, ""],
            "preis": ["1.5", "10", "2", None, "3"],
            "datum": [
                "2024-01-02",
                "2024-01-02 03:04",
                "2024-01-02 03:04:05",
                None,
                "2024-01-03",
            ],
        }
    )


@pytest.fixture()
def types(frame: pl.DataFrame) -> dict[str, ColumnType]:
    return {
        "name": ColumnType.TEXT,
        "preis": ColumnType.NUMBER,
        "datum": ColumnType.DATE,
    }


def test_text_contains_is_case_insensitive(
    frame: pl.DataFrame, types: dict[str, ColumnType]
) -> None:
    result = apply_query(
        frame, types, [Filter("name", FilterOperator.CONTAINS, "APF")]
    )
    assert result.get_column("name").to_list() == ["Apfel"]

    umlaut = apply_query(
        frame, types, [Filter("name", FilterOperator.CONTAINS, "ÄPF")]
    )
    assert umlaut.get_column("name").to_list() == ["Äpfel"]


def test_text_contains_keeps_sharp_s() -> None:
    frame = pl.DataFrame({"name": ["Straße", "Strasse"]})
    types = {"name": ColumnType.TEXT}
    result = apply_query(
        frame, types, [Filter("name", FilterOperator.CONTAINS, "straße")]
    )
    assert result.get_column("name").to_list() == ["Straße"]


def test_text_equals_and_not_equals(
    frame: pl.DataFrame, types: dict[str, ColumnType]
) -> None:
    equals = apply_query(
        frame, types, [Filter("name", FilterOperator.EQUALS, "apfel")]
    )
    assert equals.get_column("name").to_list() == ["Apfel"]
    not_equals = apply_query(
        frame, types, [Filter("name", FilterOperator.NOT_EQUALS, "apfel")]
    )
    assert "Apfel" not in not_equals.get_column("name").to_list()


def test_number_comparison_uses_numeric_order(
    frame: pl.DataFrame, types: dict[str, ColumnType]
) -> None:
    result = apply_query(
        frame, types, [Filter("preis", FilterOperator.GREATER, "2")]
    )
    assert result.get_column("preis").to_list() == ["10", "3"]

    result = apply_query(
        frame, types, [Filter("preis", FilterOperator.LESS_EQUAL, "2")]
    )
    assert result.get_column("preis").to_list() == ["1.5", "2"]


def test_date_filters_cover_both_forms(
    frame: pl.DataFrame, types: dict[str, ColumnType]
) -> None:
    before = apply_query(
        frame, types, [Filter("datum", FilterOperator.BEFORE, "2024-01-02 03:04:05")]
    )
    assert before.get_column("datum").to_list() == [
        "2024-01-02",
        "2024-01-02 03:04",
    ]

    equals = apply_query(
        frame, types, [Filter("datum", FilterOperator.EQUALS, "2024-01-02")]
    )
    assert equals.get_column("datum").to_list() == ["2024-01-02"]

    after = apply_query(
        frame, types, [Filter("datum", FilterOperator.AFTER, "2024-01-02 03:04:05")]
    )
    assert after.get_column("datum").to_list() == ["2024-01-03"]


def test_empty_and_not_empty(
    frame: pl.DataFrame, types: dict[str, ColumnType]
) -> None:
    empty = apply_query(frame, types, [Filter("preis", FilterOperator.IS_EMPTY)])
    assert empty.height == 1
    filled = apply_query(
        frame, types, [Filter("preis", FilterOperator.IS_NOT_EMPTY)]
    )
    assert filled.height == 4


def test_filters_are_combined_with_and(
    frame: pl.DataFrame, types: dict[str, ColumnType]
) -> None:
    result = apply_query(
        frame,
        types,
        [
            Filter("preis", FilterOperator.GREATER, "1"),
            Filter("datum", FilterOperator.BEFORE, "2024-01-03"),
        ],
    )
    assert result.get_column("name").to_list() == ["Apfel", "birne", "Äpfel"]


def test_original_frame_is_unchanged(
    frame: pl.DataFrame, types: dict[str, ColumnType]
) -> None:
    before = frame.clone()
    apply_query(
        frame,
        types,
        [Filter("name", FilterOperator.CONTAINS, "a")],
        SortSpec("preis", True),
    )
    assert frame.equals(before)


def test_invalid_values_raise_query_error() -> None:
    with pytest.raises(QueryError):
        parse_number("zehn")
    with pytest.raises(QueryError):
        parse_date("02.01.2024")
    with pytest.raises(QueryError):
        parse_date("2024-02-30")
    with pytest.raises(QueryError):
        build_filter_expr(
            "preis", ColumnType.NUMBER, FilterOperator.GREATER, ""
        )
    with pytest.raises(QueryError):
        build_filter_expr("name", ColumnType.TEXT, FilterOperator.CONTAINS, "  ")
    with pytest.raises(QueryError):
        build_filter_expr(
            "name", ColumnType.TEXT, FilterOperator.GREATER, "1"
        )


def test_unknown_column_raises_query_error(
    frame: pl.DataFrame, types: dict[str, ColumnType]
) -> None:
    with pytest.raises(QueryError):
        apply_query(frame, types, [Filter("fehlt", FilterOperator.CONTAINS, "a")])


def test_sort_numbers_puts_empty_last(
    frame: pl.DataFrame, types: dict[str, ColumnType]
) -> None:
    ascending = apply_query(frame, types, sort=SortSpec("preis"))
    assert ascending.get_column("preis").to_list() == [
        "1.5",
        "2",
        "3",
        "10",
        None,
    ]
    descending = apply_query(
        frame, types, sort=SortSpec("preis", True)
    )
    assert descending.get_column("preis").to_list() == [
        "10",
        "3",
        "2",
        "1.5",
        None,
    ]


def test_sort_dates_puts_empty_last(
    frame: pl.DataFrame, types: dict[str, ColumnType]
) -> None:
    ascending = apply_query(frame, types, sort=SortSpec("datum"))
    assert ascending.get_column("datum").to_list() == [
        "2024-01-02",
        "2024-01-02 03:04",
        "2024-01-02 03:04:05",
        "2024-01-03",
        None,
    ]


def test_sort_text_ignores_case_and_puts_empty_last(
    frame: pl.DataFrame, types: dict[str, ColumnType]
) -> None:
    ascending = apply_query(frame, types, sort=SortSpec("name"))
    assert ascending.get_column("name").to_list() == [
        "Apfel",
        "birne",
        "Äpfel",
        None,
        "",
    ]
