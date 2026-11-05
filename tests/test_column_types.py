from __future__ import annotations

import polars as pl

from csv_dis.column_types import ColumnType, detect_column_type, detect_column_types


def _series(values: list[str | None]) -> pl.Series:
    return pl.Series("x", values, dtype=pl.String)


def test_numbers_are_recognized() -> None:
    values = _series(["1", "-2.5", "0", "10", "+3", "0.25", None, ""])
    assert detect_column_type(values) is ColumnType.NUMBER


def test_leading_zero_or_unit_makes_text() -> None:
    assert detect_column_type(_series(["007"])) is ColumnType.TEXT
    assert detect_column_type(_series(["432 Mbit/s"])) is ColumnType.TEXT
    assert detect_column_type(_series(["1.", ".5", "1,5"])) is ColumnType.TEXT


def test_dates_are_recognized() -> None:
    values = _series(
        [
            "2024-01-02",
            "2024-01-02 03:04",
            "2024-01-02 03:04:05",
            "",
            None,
        ]
    )
    assert detect_column_type(values) is ColumnType.DATE


def test_invalid_calendar_date_makes_text() -> None:
    assert detect_column_type(_series(["2024-02-30"])) is ColumnType.TEXT
    assert detect_column_type(_series(["2024-01-02 25:00"])) is ColumnType.TEXT


def test_other_date_forms_make_text() -> None:
    assert detect_column_type(_series(["02.01.2024"])) is ColumnType.TEXT
    assert detect_column_type(_series(["2024-1-2"])) is ColumnType.TEXT
    assert detect_column_type(_series(["2024-01-02T03:04"])) is ColumnType.TEXT


def test_mixed_and_empty_columns_are_text() -> None:
    assert detect_column_type(_series(["1", "zwei"])) is ColumnType.TEXT
    assert detect_column_type(_series([None, ""])) is ColumnType.TEXT


def test_detect_column_types_keeps_column_order() -> None:
    frame = pl.DataFrame(
        {
            "preis": ["1", "2"],
            "name": ["a", "b"],
            "datum": ["2024-01-01", "2024-01-02"],
        }
    )
    assert detect_column_types(frame) == {
        "preis": ColumnType.NUMBER,
        "name": ColumnType.TEXT,
        "datum": ColumnType.DATE,
    }
