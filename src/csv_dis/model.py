"""Qt-Tabellenmodell über einem Polars-DataFrame."""

from __future__ import annotations

import polars as pl
from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt6.QtGui import QBrush, QColor

from .column_types import ColumnType, column_type_label
from .search import SearchHits

_HIT_BRUSH = QBrush(QColor("#fff3bf"))
_CURRENT_HIT_BRUSH = QBrush(QColor("#ffd43b"))
_HIT_TEXT_BRUSH = QBrush(QColor("#1f1f1f"))


class CsvTableModel(QAbstractTableModel):
    """Read-only-Modell; nur sichtbare Zellen werden abgefragt."""

    def __init__(
        self,
        frame: pl.DataFrame,
        parent=None,
        *,
        types: dict[str, ColumnType] | None = None,
        filtered: frozenset[str] = frozenset(),
        hits: SearchHits | None = None,
    ) -> None:
        super().__init__(parent)
        self._frame = frame
        self._columns = [frame.get_column(name) for name in frame.columns]
        self._types = types or {}
        self._filtered = filtered
        self._hits = hits
        self._current_row: int | None = None

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else self._frame.height

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else self._frame.width

    def column_name(self, section: int) -> str:
        return self._frame.columns[section]

    def frame(self) -> pl.DataFrame:
        return self._frame

    def set_search_hits(
        self, hits: SearchHits | None, current_row: int | None = None
    ) -> None:
        self._hits = hits
        self._current_row = current_row
        if self.columnCount() == 0 or self.rowCount() == 0:
            return
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(self.rowCount() - 1, self.columnCount() - 1),
            [Qt.ItemDataRole.BackgroundRole],
        )

    def set_current_row(self, row: int | None) -> None:
        if row == self._current_row:
            return
        previous = self._current_row
        self._current_row = row
        self._repaint_rows(previous)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._columns[index.column()][index.row()]
            return "" if value is None else str(value)
        if role == Qt.ItemDataRole.BackgroundRole and self._hits is not None:
            column = self._frame.columns[index.column()]
            if self._hits.cell_hit(index.row(), column):
                if index.row() == self._current_row:
                    return _CURRENT_HIT_BRUSH
                return _HIT_BRUSH
        if role == Qt.ItemDataRole.ForegroundRole and self._hits is not None:
            column = self._frame.columns[index.column()]
            if self._hits.cell_hit(index.row(), column):
                return _HIT_TEXT_BRUSH
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        if orientation != Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                return str(section + 1)
            return None

        name = self._frame.columns[section]
        if role == Qt.ItemDataRole.DisplayRole:
            return f"{name} ▾" if name in self._filtered else name
        if role == Qt.ItemDataRole.ToolTipRole:
            parts = [name]
            column_type = self._types.get(name)
            if column_type is not None:
                parts.append(f"Typ: {column_type_label(column_type)}")
            if name in self._filtered:
                parts.append("Gefiltert; Doppelklick zum Ändern")
            else:
                parts.append("Doppelklick zum Filtern")
            return "\n".join(parts)
        return None

    def _repaint_rows(self, previous_row: int | None) -> None:
        if self.columnCount() == 0 or self.rowCount() == 0:
            return
        last_column = self.columnCount() - 1
        rows: set[int] = set()
        if previous_row is not None:
            rows.add(previous_row)
        if self._current_row is not None:
            rows.add(self._current_row)
        for row in rows:
            if 0 <= row < self.rowCount():
                self.dataChanged.emit(
                    self.index(row, 0),
                    self.index(row, last_column),
                    [Qt.ItemDataRole.BackgroundRole],
                )
