"""Erkannte Spaltentypen aus den Werten einer Spalte ableiten.

Der Typ dient nur der Sortierung und den Filteroperatoren. Angezeigt wird
immer der Originaltext.
"""

from __future__ import annotations

import re
from enum import Enum

import polars as pl


class ColumnType(str, Enum):
    NUMBER = "number"
    DATE = "date"
    TEXT = "text"


TYPE_LABELS = {
    ColumnType.NUMBER: "Zahl",
    ColumnType.DATE: "Datum",
    ColumnType.TEXT: "Text",
}

# Optionales Vorzeichen, Ziffern, optional genau ein Dezimalpunkt. Führende
# Nullen ("007") und Einheiten ("432 Mbit/s") passen bewusst nicht.
_NUMBER_PATTERN = r"^[+-]?(?:0|[1-9]\d*)(?:\.\d+)?$"

# Ausschließlich YYYY-MM-DD oder YYYY-MM-DD HH:MM[:SS].
_DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2}(?::\d{2})?)?$"


def column_type_label(column_type: ColumnType) -> str:
    return TYPE_LABELS[column_type]


def detect_column_types(frame: pl.DataFrame) -> dict[str, ColumnType]:
    """Bestimmt pro Spalte den Typ aus allen nicht leeren Werten."""
    return {
        name: detect_column_type(frame.get_column(name))
        for name in frame.columns
    }


def detect_column_type(values: pl.Series) -> ColumnType:
    """Leere Zellen zählen nicht mit; leere und gemischte Spalten sind Text."""
    filled = values.drop_nulls()
    filled = filled.filter(filled != "")
    if filled.len() == 0:
        return ColumnType.TEXT
    if _all_match(filled, _NUMBER_PATTERN):
        return ColumnType.NUMBER
    if _all_match(filled, _DATE_PATTERN) and _dates_are_valid(filled):
        return ColumnType.DATE
    return ColumnType.TEXT


def _all_match(values: pl.Series, pattern: str) -> bool:
    return bool(values.str.contains(pattern).all())


def _dates_are_valid(values: pl.Series) -> bool:
    """Prüft zusätzlich zum Muster, ob Kalenderdatum und Uhrzeit existieren."""
    dates = values.str.slice(0, 10).str.strptime(
        pl.Date, "%Y-%m-%d", strict=False
    )
    if dates.null_count():
        return False

    with_time = values.str.len_chars() > 10
    if not with_time.any():
        return True

    times = values.filter(with_time).str.slice(11)
    normalized = (
        times.to_frame("uhrzeit")
        .select(
            pl.when(pl.col("uhrzeit").str.len_chars() == 5)
            .then(pl.col("uhrzeit") + ":00")
            .otherwise(pl.col("uhrzeit"))
            .alias("uhrzeit")
        )
        .to_series()
    )
    parsed = normalized.str.strptime(pl.Time, "%H:%M:%S", strict=False)
    return parsed.null_count() == 0
