"""Spaltenübergreifende Suche über die sichtbare Ansicht.

Ein Treffer ist eine Zeile, in der jeder Suchbegriff mindestens einmal in einer
sichtbaren Spalte vorkommt. Die Suche ändert den DataFrame nicht.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import polars as pl


@dataclass(frozen=True)
class SearchHits:
    """Treffer einer Suche, ausgerichtet auf die Zeilen der Ansicht."""

    rows: pl.Series = field(
        default_factory=lambda: pl.Series("zeile", [], dtype=pl.UInt32)
    )
    cells: dict[str, pl.Series] = field(default_factory=dict)
    terms: tuple[str, ...] = ()

    @property
    def count(self) -> int:
        return len(self.rows)

    def row_at(self, index: int) -> int:
        return int(self.rows.item(index))

    def cell_hit(self, row: int, column: str) -> bool:
        mask = self.cells.get(column)
        if mask is None or row < 0 or row >= len(mask):
            return False
        return bool(mask.item(row))

    def first_column(self, row: int, columns: list[str]) -> str | None:
        for column in columns:
            if self.cell_hit(row, column):
                return column
        return None


def split_terms(text: str) -> tuple[str, ...]:
    """Zerlegt die Eingabe an Leerzeichen; leere Begriffe zählen nicht."""
    return tuple(part for part in text.split() if part)


def search_frame(
    frame: pl.DataFrame, columns: list[str], text: str
) -> SearchHits:
    """Sucht in `columns` nach allen Begriffen aus `text` (UND, Zeilen)."""
    terms = split_terms(text)
    if not terms or not columns or frame.height == 0:
        return SearchHits()

    cell_any: pl.DataFrame | None = None
    row_all: pl.Series | None = None

    for term in terms:
        needle = term.lower()
        part = frame.select(
            [
                pl.col(column)
                .cast(pl.Utf8, strict=False)
                .str.to_lowercase()
                .str.contains(needle, literal=True)
                .fill_null(False)
                .alias(column)
                for column in columns
            ]
        )
        if cell_any is None:
            cell_any = part
        else:
            cell_any = pl.DataFrame(
                {column: cell_any[column] | part[column] for column in columns}
            )
        term_rows = part.select(
            pl.any_horizontal(pl.all()).alias("__treffer")
        )["__treffer"]
        row_all = term_rows if row_all is None else row_all & term_rows

    if row_all is None or int(row_all.sum()) == 0 or cell_any is None:
        return SearchHits(terms=terms)

    rows = row_all.arg_true()
    cells = {
        column: (cell_any[column] & row_all).alias(column)
        for column in columns
    }
    return SearchHits(rows=rows, cells=cells, terms=terms)
