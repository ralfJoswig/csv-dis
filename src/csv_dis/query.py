"""Filter und Sortierung als Polars-Ausdrücke, ohne GUI.

Die Funktionen geben neue DataFrames zurück; der übergebene DataFrame bleibt
unverändert. Leere Zellen sind im geladenen DataFrame `null`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import polars as pl

from .column_types import ColumnType

_NUMBER_VALUE = re.compile(r"^[+-]?(?:\d+(?:\.\d+)?|\.\d+)$")
_DATE_VALUE = re.compile(
    r"^\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2}(?::\d{2})?)?$"
)


class QueryError(Exception):
    """Ungültige Filtereingabe; die Meldung ist für den Benutzer gedacht."""


class FilterOperator(str, Enum):
    CONTAINS = "contains"
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    LESS = "less"
    LESS_EQUAL = "less_equal"
    GREATER = "greater"
    GREATER_EQUAL = "greater_equal"
    BEFORE = "before"
    AFTER = "after"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"


OPERATOR_LABELS = {
    FilterOperator.CONTAINS: "enthält",
    FilterOperator.EQUALS: "ist gleich",
    FilterOperator.NOT_EQUALS: "ist ungleich",
    FilterOperator.LESS: "<",
    FilterOperator.LESS_EQUAL: "≤",
    FilterOperator.GREATER: ">",
    FilterOperator.GREATER_EQUAL: "≥",
    FilterOperator.BEFORE: "vor",
    FilterOperator.AFTER: "nach",
    FilterOperator.IS_EMPTY: "ist leer",
    FilterOperator.IS_NOT_EMPTY: "ist nicht leer",
}

OPERATORS_BY_TYPE: dict[ColumnType, tuple[FilterOperator, ...]] = {
    ColumnType.TEXT: (
        FilterOperator.CONTAINS,
        FilterOperator.EQUALS,
        FilterOperator.NOT_EQUALS,
        FilterOperator.IS_EMPTY,
        FilterOperator.IS_NOT_EMPTY,
    ),
    ColumnType.NUMBER: (
        FilterOperator.EQUALS,
        FilterOperator.NOT_EQUALS,
        FilterOperator.LESS,
        FilterOperator.LESS_EQUAL,
        FilterOperator.GREATER,
        FilterOperator.GREATER_EQUAL,
        FilterOperator.IS_EMPTY,
        FilterOperator.IS_NOT_EMPTY,
    ),
    ColumnType.DATE: (
        FilterOperator.EQUALS,
        FilterOperator.BEFORE,
        FilterOperator.AFTER,
        FilterOperator.IS_EMPTY,
        FilterOperator.IS_NOT_EMPTY,
    ),
}

_VALUE_FREE_OPERATORS = (
    FilterOperator.IS_EMPTY,
    FilterOperator.IS_NOT_EMPTY,
)


@dataclass(frozen=True)
class Filter:
    column: str
    operator: FilterOperator
    value: str = ""


@dataclass(frozen=True)
class SortSpec:
    column: str
    descending: bool = False


def operator_label(operator: FilterOperator) -> str:
    return OPERATOR_LABELS[operator]


def operators_for(column_type: ColumnType) -> tuple[FilterOperator, ...]:
    return OPERATORS_BY_TYPE[column_type]


def needs_value(operator: FilterOperator) -> bool:
    return operator not in _VALUE_FREE_OPERATORS


def filter_label(active: Filter) -> str:
    if not needs_value(active.operator):
        return (
            f"{active.column} {operator_label(active.operator)}"
        )
    return (
        f"{active.column} {operator_label(active.operator)} {active.value}"
    )


def apply_query(
    frame: pl.DataFrame,
    types: dict[str, ColumnType],
    filters: list[Filter] | tuple[Filter, ...] = (),
    sort: SortSpec | None = None,
) -> pl.DataFrame:
    """Wendet alle Filter (UND) und die Sortierung an."""
    result = frame
    for active in filters:
        result = result.filter(
            build_filter_expr(
                active.column,
                _type_of(types, active.column),
                active.operator,
                active.value,
            )
        )
    if sort is not None:
        result = sort_frame(
            result, sort.column, _type_of(types, sort.column), sort.descending
        )
    return result


def build_filter_expr(
    column: str,
    column_type: ColumnType,
    operator: FilterOperator,
    value: str = "",
) -> pl.Expr:
    """Baut einen einzelnen Filterausdruck und prüft den Wert."""
    if operator not in OPERATORS_BY_TYPE[column_type]:
        raise QueryError(
            f"Der Operator {operator_label(operator)} passt nicht zum "
            f"Spaltentyp {_type_label(column_type)}."
        )
    if operator is FilterOperator.IS_EMPTY:
        return _is_empty(column)
    if operator is FilterOperator.IS_NOT_EMPTY:
        return _is_empty(column).not_()

    if column_type is ColumnType.NUMBER:
        number = parse_number(value)
        field = pl.col(column).cast(pl.Float64, strict=False)
        comparisons = {
            FilterOperator.EQUALS: field == number,
            FilterOperator.NOT_EQUALS: field != number,
            FilterOperator.LESS: field < number,
            FilterOperator.LESS_EQUAL: field <= number,
            FilterOperator.GREATER: field > number,
            FilterOperator.GREATER_EQUAL: field >= number,
        }
        return comparisons[operator]

    if column_type is ColumnType.DATE:
        moment = parse_date(value)
        field = _date_expr(column)
        comparisons = {
            FilterOperator.EQUALS: field == moment,
            FilterOperator.BEFORE: field < moment,
            FilterOperator.AFTER: field > moment,
        }
        return comparisons[operator]

    text = value.lower()
    if not value.strip():
        raise QueryError("Bitte einen Wert eingeben.")
    field = pl.col(column).str.to_lowercase()
    comparisons = {
        FilterOperator.CONTAINS: field.str.contains(text, literal=True),
        FilterOperator.EQUALS: field == text,
        FilterOperator.NOT_EQUALS: field != text,
    }
    return comparisons[operator]


def sort_frame(
    frame: pl.DataFrame,
    column: str,
    column_type: ColumnType,
    descending: bool = False,
) -> pl.DataFrame:
    """Sortiert nach genau einer Spalte; leere Zellen stehen immer am Ende."""
    if column not in frame.columns:
        raise QueryError(f"Unbekannte Spalte: {column}")

    empty = _is_empty(column).alias("__leer")
    if column_type is ColumnType.NUMBER:
        key = (
            pl.col(column).cast(pl.Float64, strict=False).alias("__schluessel")
        )
    elif column_type is ColumnType.DATE:
        key = _date_expr(column).alias("__schluessel")
    else:
        key = pl.col(column).str.to_lowercase().alias("__schluessel")

    return (
        frame.with_columns(key, empty)
        .sort(
            ["__leer", "__schluessel"],
            descending=[False, descending],
            maintain_order=True,
        )
        .drop(["__leer", "__schluessel"])
    )


def parse_number(value: str) -> float:
    text = value.strip()
    if not _NUMBER_VALUE.match(text):
        raise QueryError(f"„{value}“ ist keine gültige Zahl.")
    return float(text)


def parse_date(value: str) -> datetime:
    text = value.strip()
    if not _DATE_VALUE.match(text):
        raise QueryError(
            f"„{value}“ ist kein gültiges Datum (YYYY-MM-DD oder "
            "YYYY-MM-DD HH:MM[:SS])."
        )
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise QueryError(f"„{value}“ ist kein gültiges Datum.") from exc


def _type_of(types: dict[str, ColumnType], column: str) -> ColumnType:
    try:
        return types[column]
    except KeyError:
        raise QueryError(f"Unbekannte Spalte: {column}") from None


def _type_label(column_type: ColumnType) -> str:
    from .column_types import column_type_label

    return column_type_label(column_type)


def _is_empty(column: str) -> pl.Expr:
    return pl.col(column).is_null() | (pl.col(column) == "")


def _date_expr(column: str) -> pl.Expr:
    """Parst beide erlaubten Datumsformen in eine vergleichbare Spalte."""
    text = pl.col(column)
    return pl.coalesce(
        [
            text.str.strptime(
                pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False
            ),
            (text + ":00").str.strptime(
                pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False
            ),
            text.str.strptime(pl.Datetime, "%Y-%m-%d", strict=False),
        ]
    )
