"""Hauptfenster: Datei öffnen, filtern, sortieren, Spalten ausblenden."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path

import polars as pl
from PyQt6.QtCore import QObject, QRunnable, Qt, QThreadPool, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QAction,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QKeySequence,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from .column_types import ColumnType, detect_column_types
from .csv_loader import (
    CsvLoadError,
    LoadResult,
    delimiter_label,
    encoding_label,
    load_csv,
)
from .about_dialog import AboutDialog
from .filter_dialog import FilterDialog
from .header import FilterHeader
from .model import CsvTableModel
from .parser_dialog import ParserDialog
from .query import (
    Filter,
    QueryError,
    SortSpec,
    apply_query,
    filter_label,
)
from .resources import app_icon
from .search import SearchHits, search_frame
from .search_bar import SearchBar

DELAY_MS = 200


class _QuerySignals(QObject):
    done = pyqtSignal(int, object, object)


class _QueryTask(QRunnable):
    """Berechnet Filter und Sortierung außerhalb des GUI-Threads."""

    def __init__(
        self,
        generation: int,
        frame: pl.DataFrame,
        types: dict[str, ColumnType],
        filters: tuple[Filter, ...],
        sort: SortSpec | None,
        cancel: threading.Event,
        signals: _QuerySignals,
    ) -> None:
        super().__init__()
        self._generation = generation
        self._frame = frame
        self._types = types
        self._filters = filters
        self._sort = sort
        self._cancel = cancel
        self._signals = signals

    def run(self) -> None:
        if self._cancel.is_set():
            return
        try:
            result = apply_query(
                self._frame, self._types, self._filters, self._sort
            )
        except QueryError as exc:
            if not self._cancel.is_set():
                self._signals.done.emit(self._generation, None, str(exc))
            return
        except Exception as exc:  # noqa: BLE001 - im GUI als Meldung zeigen
            if not self._cancel.is_set():
                self._signals.done.emit(
                    self._generation,
                    None,
                    f"Interner Fehler: {exc}",
                )
            return
        if self._cancel.is_set():
            return
        self._signals.done.emit(self._generation, result, None)


@dataclass(frozen=True)
class _Loaded:
    path: Path
    result: LoadResult
    types: dict[str, ColumnType]


class _SearchSignals(QObject):
    done = pyqtSignal(int, object, object)


class _SearchTask(QRunnable):
    """Berechnet die Treffer einer Suche außerhalb des GUI-Threads."""

    def __init__(
        self,
        generation: int,
        frame: pl.DataFrame,
        columns: list[str],
        text: str,
        cancel: threading.Event,
        signals: _SearchSignals,
    ) -> None:
        super().__init__()
        self._generation = generation
        self._frame = frame
        self._columns = columns
        self._text = text
        self._cancel = cancel
        self._signals = signals

    def run(self) -> None:
        if self._cancel.is_set():
            return
        try:
            hits = search_frame(self._frame, self._columns, self._text)
        except Exception as exc:  # noqa: BLE001 - im GUI als Meldung zeigen
            if not self._cancel.is_set():
                self._signals.done.emit(
                    self._generation,
                    None,
                    f"Suche fehlgeschlagen: {exc}",
                )
            return
        if self._cancel.is_set():
            return
        self._signals.done.emit(self._generation, hits, None)


class _LoadSignals(QObject):
    done = pyqtSignal(int, object, object)


class _LoadTask(QRunnable):
    """Lädt Datei und Typerkennung außerhalb des GUI-Threads."""

    def __init__(
        self,
        generation: int,
        path: Path,
        delimiter: str | None,
        encoding: str | None,
        cancel: threading.Event,
        signals: _LoadSignals,
    ) -> None:
        super().__init__()
        self._generation = generation
        self._path = path
        self._delimiter = delimiter
        self._encoding = encoding
        self._cancel = cancel
        self._signals = signals

    def run(self) -> None:
        if self._cancel.is_set():
            return
        try:
            result = load_csv(
                self._path,
                delimiter=self._delimiter,
                encoding=self._encoding,
            )
        except CsvLoadError as exc:
            if not self._cancel.is_set():
                self._signals.done.emit(self._generation, None, str(exc))
            return
        except Exception as exc:  # noqa: BLE001 - im GUI als Meldung zeigen
            if not self._cancel.is_set():
                self._signals.done.emit(
                    self._generation,
                    None,
                    f"Interner Fehler: {exc}",
                )
            return
        if self._cancel.is_set():
            return
        try:
            types = detect_column_types(result.frame)
        except Exception as exc:  # noqa: BLE001
            if not self._cancel.is_set():
                self._signals.done.emit(
                    self._generation,
                    None,
                    f"Spaltentypen konnten nicht erkannt werden: {exc}",
                )
            return
        if self._cancel.is_set():
            return
        self._signals.done.emit(
            self._generation, _Loaded(self._path, result, types), None
        )


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("csv-dis")
        self.setWindowIcon(app_icon())
        self.resize(1200, 760)
        self.setAcceptDrops(True)

        self._full_frame: pl.DataFrame | None = None
        self._view_frame: pl.DataFrame | None = None
        self._types: dict[str, ColumnType] = {}
        self._filters: list[Filter] = []
        self._sort: SortSpec | None = None
        self._hidden: set[str] = set()
        self._file_info = ""
        self._generation = 0
        self._cancel_token: threading.Event | None = None
        self._active_signals: _QuerySignals | None = None
        self._load_generation = 0
        self._load_cancel: threading.Event | None = None
        self._load_signals: _LoadSignals | None = None
        self._progress: QProgressDialog | None = None
        self._pending_notice: str | None = None
        self._path: Path | None = None
        self._delimiter: str | None = None
        self._encoding: str | None = None
        self._pool = QThreadPool.globalInstance()

        self._search_generation = 0
        self._search_cancel: threading.Event | None = None
        self._search_signals: _SearchSignals | None = None
        self._hits: SearchHits | None = None
        self._hit_index = -1

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(DELAY_MS)
        self._timer.timeout.connect(self._start_query)

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(DELAY_MS)
        self._search_timer.timeout.connect(self._start_search)

        self._build_ui()
        self._build_menu()
        self._update_status()

    # ------------------------------------------------------------------ Aufbau

    def _build_ui(self) -> None:
        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.filter_bar = QWidget(central)
        self.filter_bar.setObjectName("filter_bar")
        self._filter_layout = QHBoxLayout(self.filter_bar)
        self._filter_layout.setContentsMargins(6, 4, 6, 4)
        self._filter_layout.setSpacing(6)
        self.filter_bar.hide()
        layout.addWidget(self.filter_bar)

        self.search_bar = SearchBar(central)
        self.search_bar.setEnabled(False)
        self.search_bar.textChanged.connect(self._search_text_changed)
        self.search_bar.nextRequested.connect(self.next_hit)
        self.search_bar.previousRequested.connect(self.previous_hit)
        self.search_bar.escapePressed.connect(self._clear_search)
        layout.addWidget(self.search_bar)

        self.table = QTableView(central)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)
        self.table.setWordWrap(False)
        self.table.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectItems
        )
        self.table.verticalHeader().setDefaultSectionSize(22)
        self.table.setHorizontalHeader(FilterHeader(self.table))
        self.table.horizontalHeader().setDefaultSectionSize(140)
        layout.addWidget(self.table)
        self.setCentralWidget(central)

        header = self.table.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.sectionClicked.connect(self._header_clicked)
        header.sectionDoubleClicked.connect(self._header_double_clicked)
        header.filterRequested.connect(self._filter_section)
        header.customContextMenuRequested.connect(self._header_menu)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&Datei")

        open_action = QAction("&Öffnen…", self)
        open_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Open))
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        self._parser_action = QAction("Trennzeichen und Encoding…", self)
        self._parser_action.setEnabled(False)
        self._parser_action.triggered.connect(self.correct_parser)
        file_menu.addAction(self._parser_action)

        file_menu.addSeparator()

        quit_action = QAction("&Beenden", self)
        quit_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Quit))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        view_menu = self.menuBar().addMenu("&Ansicht")
        show_all = QAction("Alle Spalten einblenden", self)
        show_all.triggered.connect(self.show_all_columns)
        view_menu.addAction(show_all)

        self._find_action = QAction("&Suchen", self)
        self._find_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Find))
        self._find_action.triggered.connect(self._focus_search)
        view_menu.addAction(self._find_action)

        clear_filters = QAction("Alle Filter entfernen", self)
        clear_filters.triggered.connect(self.clear_filters)
        view_menu.addAction(clear_filters)

        clear_sort = QAction("Sortierung aufheben", self)
        clear_sort.triggered.connect(self.clear_sort)
        view_menu.addAction(clear_sort)

        help_menu = self.menuBar().addMenu("&Hilfe")
        about_action = QAction("Über csv-dis", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    # ------------------------------------------------------------------ Laden

    def open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "CSV-Datei öffnen",
            "",
            "CSV-Dateien (*.csv *.txt);;Alle Dateien (*)",
        )
        if path:
            self.open_path(Path(path))

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._dropped_paths(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if self._dropped_paths(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = self._dropped_paths(event.mimeData())
        if not paths:
            event.ignore()
            return

        event.acceptProposedAction()
        self.open_path(paths[0])
        if len(paths) > 1:
            message = (
                f"Nur die erste Datei wurde geöffnet; "
                f"{len(paths) - 1} weitere ignoriert."
            )
            self._pending_notice = message
            self.statusBar().showMessage(message, 5000)
            QTimer.singleShot(5000, self._update_status)

    @staticmethod
    def _dropped_paths(mime) -> list[Path]:
        if not mime.hasUrls():
            return []
        paths: list[Path] = []
        for url in mime.urls():
            if not url.isLocalFile():
                continue
            path = Path(url.toLocalFile())
            if path.is_file():
                paths.append(path)
        return paths

    def load_path(
        self,
        path: Path,
        *,
        delimiter: str | None = None,
        encoding: str | None = None,
    ) -> bool:
        """Lädt synchron; für Tests und direkte Aufrufe."""
        self._load_generation += 1
        if self._load_cancel is not None:
            self._load_cancel.set()
        self._close_progress()
        try:
            result = load_csv(path, delimiter=delimiter, encoding=encoding)
            types = detect_column_types(result.frame)
        except CsvLoadError as exc:
            QMessageBox.critical(self, "Datei konnte nicht geöffnet werden", str(exc))
            return False

        self._apply_loaded(_Loaded(path, result, types))
        return True

    def open_path(
        self,
        path: Path,
        *,
        delimiter: str | None = None,
        encoding: str | None = None,
    ) -> None:
        """Lädt im Hintergrund und zeigt dabei eine Fortschrittsanzeige."""
        self._load_generation += 1
        generation = self._load_generation
        if self._load_cancel is not None:
            self._load_cancel.set()
        self._close_progress()

        progress = QProgressDialog(
            "Datei wird geladen…", "Abbrechen", 0, 0, self
        )
        progress.setWindowTitle("CSV-Datei öffnen")
        progress.setWindowModality(Qt.WindowModality.NonModal)
        progress.setMinimumDuration(0)
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        progress.setValue(0)
        progress.show()
        self._progress = progress

        token = threading.Event()
        self._load_cancel = token
        progress.canceled.connect(lambda: self._cancel_load(token))

        signals = _LoadSignals()
        signals.done.connect(self._load_done)
        self._load_signals = signals
        self._pool.start(
            _LoadTask(
                generation, path, delimiter, encoding, token, signals
            )
        )

    def _cancel_load(self, token: threading.Event) -> None:
        token.set()
        self._close_progress()

    def _close_progress(self) -> None:
        progress = self._progress
        if progress is None:
            return
        self._progress = None
        progress.blockSignals(True)
        progress.close()
        progress.deleteLater()

    def _load_done(
        self, generation: int, payload: _Loaded | None, error: str | None
    ) -> None:
        if generation != self._load_generation:
            return
        self._close_progress()
        if error is not None:
            self._pending_notice = None
            QMessageBox.critical(
                self, "Datei konnte nicht geöffnet werden", error
            )
            return
        if payload is None:
            return
        self._apply_loaded(payload)

    def _apply_loaded(self, loaded: _Loaded) -> None:
        result = loaded.result
        self._full_frame = result.frame
        self._types = loaded.types
        self._filters.clear()
        self._sort = None
        self._hidden.clear()
        self._file_info = (
            f"Trennzeichen {delimiter_label(result.delimiter)} · "
            f"{encoding_label(result.encoding)}"
        )
        self._path = loaded.path
        self._delimiter = result.delimiter
        self._encoding = result.encoding.encoding
        self._parser_action.setEnabled(True)
        self._reset_search()
        self.search_bar.setEnabled(True)
        self.setWindowTitle(f"{loaded.path.name} – csv-dis")
        self.apply_now()
        if self._pending_notice is not None:
            notice = self._pending_notice
            self._pending_notice = None
            self.statusBar().showMessage(notice, 5000)
            QTimer.singleShot(5000, self._update_status)
        if result.warnings:
            QMessageBox.warning(
                self, "Hinweise beim Laden", "\n".join(result.warnings)
            )

    def correct_parser(self) -> None:
        """Öffnet den Dialog und lädt die aktuelle Datei mit den neuen Werten."""
        if (
            self._path is None
            or self._delimiter is None
            or self._encoding is None
        ):
            return
        dialog = ParserDialog(
            self._path, self._delimiter, self._encoding, self
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self.open_path(
            self._path,
            delimiter=dialog.chosen_delimiter(),
            encoding=dialog.chosen_encoding(),
        )

    # ------------------------------------------------------------------ Suche

    def _show_about(self) -> None:
        AboutDialog(self).exec()

    def _focus_search(self) -> None:
        if self.search_bar.isEnabled():
            self.search_bar.focus_edit()

    def _search_text_changed(self, text: str) -> None:
        self._search_timer.stop()
        self._search_generation += 1
        if self._search_cancel is not None:
            self._search_cancel.set()
        self._set_hits(None)
        self._update_search_counter()
        if not text.strip() or self._view_frame is None:
            return
        self._search_timer.start()

    def _start_search(self) -> None:
        if self._view_frame is None:
            return
        text = self.search_bar.edit.text()
        if not text.strip():
            return
        token = threading.Event()
        self._search_cancel = token
        signals = _SearchSignals()
        signals.done.connect(self._search_done)
        self._search_signals = signals
        self._pool.start(
            _SearchTask(
                self._search_generation,
                self._view_frame,
                self._visible_columns(),
                text,
                token,
                signals,
            )
        )

    def _search_done(
        self, generation: int, hits: SearchHits | None, error: str | None
    ) -> None:
        if generation != self._search_generation:
            return
        if error is not None:
            self._hits = None
            self._hit_index = -1
            self._apply_hits_to_model()
            self.search_bar.set_counter("Fehler")
            self.search_bar.set_navigation_enabled(False)
            self.statusBar().showMessage(error, 8000)
            return
        self._hits = hits
        self._hit_index = 0 if hits is not None and hits.count else -1
        self._apply_hits_to_model()
        self._update_search_counter()
        if self._hit_index >= 0:
            self._scroll_to_hit()

    def _set_hits(self, hits: SearchHits | None) -> None:
        self._hits = hits
        self._hit_index = -1
        self._apply_hits_to_model()

    def _apply_hits_to_model(self) -> None:
        model = self.table.model()
        if model is not None:
            model.set_search_hits(self._hits, self._current_row())

    def _current_row(self) -> int | None:
        if (
            self._hits is None
            or self._hit_index < 0
            or self._hit_index >= self._hits.count
        ):
            return None
        return self._hits.row_at(self._hit_index)

    def _update_search_counter(self) -> None:
        text = self.search_bar.edit.text()
        if not text.strip() or self._view_frame is None:
            self.search_bar.set_counter("")
            self.search_bar.set_navigation_enabled(False)
            return
        if self._hits is None:
            self.search_bar.set_counter("Suche…")
            self.search_bar.set_navigation_enabled(False)
            return
        count = self._hits.count
        if count == 0:
            self.search_bar.set_counter("0 Treffer")
            self.search_bar.set_navigation_enabled(False)
            return
        self.search_bar.set_counter(
            f"{self._hit_index + 1} von {count} Treffern"
        )
        self.search_bar.set_navigation_enabled(True)

    def _navigate_hit(self, step: int) -> None:
        if self._hits is None or self._hits.count == 0:
            return
        count = self._hits.count
        if self._hit_index < 0:
            index = 0 if step > 0 else count - 1
        else:
            index = (self._hit_index + step) % count
        self._hit_index = index
        model = self.table.model()
        row = self._current_row()
        if model is not None and row is not None:
            model.set_current_row(row)
        self._update_search_counter()
        self._scroll_to_hit()

    def next_hit(self) -> None:
        self._navigate_hit(1)

    def previous_hit(self) -> None:
        self._navigate_hit(-1)

    def _scroll_to_hit(self) -> None:
        row = self._current_row()
        model = self.table.model()
        if row is None or model is None or self._hits is None:
            return
        column = self._hits.first_column(row, self._visible_columns())
        if column is None:
            section = 0
        else:
            section = model.frame().columns.index(column)
        self.table.scrollTo(
            model.index(row, section),
            QAbstractItemView.ScrollHint.PositionAtCenter,
        )

    def _visible_columns(self) -> list[str]:
        if self._view_frame is None:
            return []
        return [
            column
            for column in self._view_frame.columns
            if column not in self._hidden
        ]

    def _reset_search(self) -> None:
        self._search_timer.stop()
        self._search_generation += 1
        if self._search_cancel is not None:
            self._search_cancel.set()
        self._hits = None
        self._hit_index = -1
        self.search_bar.edit.blockSignals(True)
        self.search_bar.edit.clear()
        self.search_bar.edit.blockSignals(False)
        self.search_bar.set_counter("")
        self.search_bar.set_navigation_enabled(False)
        model = self.table.model()
        if model is not None:
            model.set_search_hits(None, None)

    def _clear_search(self) -> None:
        self.search_bar.edit.clear()
        self.table.setFocus()

    def _restart_search(self) -> None:
        self._search_timer.stop()
        self._search_generation += 1
        if self._search_cancel is not None:
            self._search_cancel.set()
        self._hits = None
        self._hit_index = -1
        self._apply_hits_to_model()
        self._update_search_counter()
        if self.search_bar.edit.text().strip():
            self._start_search()

    # -------------------------------------------------------------- Bedienung

    def toggle_sort(self, column: str) -> None:
        if self._sort is not None and self._sort.column == column:
            descending = not self._sort.descending
        else:
            descending = False
        self.set_sort(column, descending)

    def set_sort(self, column: str, descending: bool = False) -> None:
        if self._full_frame is None or column not in self._full_frame.columns:
            return
        self._sort = SortSpec(column, descending)
        self._schedule_query()

    def clear_sort(self) -> None:
        if self._sort is None:
            return
        self._sort = None
        self._schedule_query()

    def set_filter(self, active: Filter) -> None:
        """Ersetzt den Filter derselben Spalte (ein Filter pro Spalte)."""
        if self._full_frame is None or active.column not in self._full_frame.columns:
            return
        self._filters = [
            existing
            for existing in self._filters
            if existing.column != active.column
        ]
        self._filters.append(active)
        self._schedule_query()

    def remove_filter(self, active: Filter) -> None:
        if active in self._filters:
            self._filters.remove(active)
            self._schedule_query()

    def clear_filters(self) -> None:
        if not self._filters:
            return
        self._filters.clear()
        self._schedule_query()

    def set_column_visible(self, column: str, visible: bool) -> None:
        if self._full_frame is None or column not in self._full_frame.columns:
            return
        if visible:
            self._hidden.discard(column)
        else:
            self._hidden.add(column)
        self._apply_hidden()
        self._restart_search()

    def show_all_columns(self) -> None:
        self._hidden.clear()
        self._apply_hidden()
        self._restart_search()

    def open_filter_dialog(self, column: str) -> None:
        if self._full_frame is None or column not in self._full_frame.columns:
            return
        current = next(
            (
                active
                for active in reversed(self._filters)
                if active.column == column
            ),
            None,
        )
        dialog = FilterDialog(
            column, self._types.get(column, ColumnType.TEXT), current, self
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        chosen = dialog.result_filter()
        if chosen is None:
            if current is not None:
                self.remove_filter(current)
            return
        self.set_filter(chosen)

    # ---------------------------------------------------------------- Abfrage

    def _schedule_query(self) -> None:
        if self._full_frame is None:
            return
        self._generation += 1
        if self._cancel_token is not None:
            self._cancel_token.set()
        self._timer.start()

    def _start_query(self) -> None:
        if self._full_frame is None:
            return
        token = threading.Event()
        self._cancel_token = token
        signals = _QuerySignals()
        signals.done.connect(self._query_done)
        self._active_signals = signals
        task = _QueryTask(
            self._generation,
            self._full_frame,
            dict(self._types),
            tuple(self._filters),
            self._sort,
            token,
            signals,
        )
        self._pool.start(task)

    def _query_done(
        self, generation: int, frame: pl.DataFrame | None, error: str | None
    ) -> None:
        if generation != self._generation:
            return
        if error is not None:
            self.statusBar().showMessage(
                f"Filter konnte nicht angewendet werden: {error}", 8000
            )
            return
        if frame is None:
            return
        self._view_frame = frame
        self._apply_view()

    def apply_now(self) -> None:
        """Berechnet die Ansicht sofort (Laden, Tests)."""
        self._timer.stop()
        self._generation += 1
        if self._cancel_token is not None:
            self._cancel_token.set()
        if self._full_frame is None:
            return
        try:
            self._view_frame = apply_query(
                self._full_frame,
                self._types,
                self._filters,
                self._sort,
            )
        except QueryError as exc:
            self.statusBar().showMessage(
                f"Filter konnte nicht angewendet werden: {exc}", 8000
            )
            return
        self._apply_view()

    # ---------------------------------------------------------------- Ansicht

    def _apply_view(self) -> None:
        if self._view_frame is None:
            return
        self._hits = None
        self._hit_index = -1
        filtered = frozenset(active.column for active in self._filters)
        model = CsvTableModel(
            self._view_frame,
            self,
            types=self._types,
            filtered=filtered,
        )
        self.table.setModel(model)
        self._apply_hidden()
        self._apply_sort_indicator()
        self.table.horizontalHeader().set_filtered_sections(
            {
                section
                for section, name in enumerate(self._view_frame.columns)
                if name in filtered
            }
        )
        self._rebuild_filter_bar()
        self._update_status()
        self._restart_search()

    def _apply_hidden(self) -> None:
        model = self.table.model()
        if model is None:
            return
        for section in range(model.columnCount()):
            self.table.setColumnHidden(
                section, model.column_name(section) in self._hidden
            )
        self._update_status()

    def _apply_sort_indicator(self) -> None:
        header = self.table.horizontalHeader()
        model = self.table.model()
        if self._sort is None or model is None:
            header.setSortIndicatorShown(False)
            return
        columns = [
            model.column_name(section) for section in range(model.columnCount())
        ]
        if self._sort.column not in columns:
            header.setSortIndicatorShown(False)
            return
        section = columns.index(self._sort.column)
        order = (
            Qt.SortOrder.DescendingOrder
            if self._sort.descending
            else Qt.SortOrder.AscendingOrder
        )
        header.setSortIndicatorShown(True)
        header.setSortIndicator(section, order)

    def _rebuild_filter_bar(self) -> None:
        while self._filter_layout.count():
            item = self._filter_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        if not self._filters:
            self.filter_bar.hide()
            return

        for active in self._filters:
            chip = QPushButton(f"{filter_label(active)}  ✕", self.filter_bar)
            chip.setObjectName("filter_chip")
            chip.setToolTip("Filter entfernen")
            chip.setFlat(True)
            chip.clicked.connect(
                lambda _checked=False, entry=active: self.remove_filter(entry)
            )
            self._filter_layout.addWidget(chip)

        remove_all = QPushButton("Alle entfernen", self.filter_bar)
        remove_all.setObjectName("remove_all_filters")
        remove_all.setFlat(True)
        remove_all.clicked.connect(self.clear_filters)
        self._filter_layout.addWidget(remove_all)

        self._filter_layout.addStretch(1)
        self.filter_bar.show()

    def _update_status(self) -> None:
        if self._full_frame is None or self._view_frame is None:
            self.statusBar().showMessage(
                "Keine Datei geöffnet. Datei hierher ziehen oder über "
                "Datei > Öffnen… laden."
            )
            return
        parts = [
            f"{self._view_frame.height} von {self._full_frame.height} Zeilen"
        ]
        if self._hidden and len(self._hidden) >= self._full_frame.width:
            parts.append("Alle Spalten sind ausgeblendet")
        if self._file_info:
            parts.append(self._file_info)
        self.statusBar().showMessage(" · ".join(parts))

    # ----------------------------------------------------------- Kopfzeile

    def _header_clicked(self, section: int) -> None:
        model = self.table.model()
        if model is None or section >= model.columnCount():
            return
        self.toggle_sort(model.column_name(section))

    def _header_double_clicked(self, section: int) -> None:
        self._filter_section(section)

    def _filter_section(self, section: int) -> None:
        model = self.table.model()
        if model is None or section >= model.columnCount():
            return
        self.open_filter_dialog(model.column_name(section))

    def _header_menu(self, position) -> None:
        model = self.table.model()
        if model is None or self._full_frame is None:
            return
        header = self.table.horizontalHeader()
        section = header.logicalIndexAt(position)
        menu = QMenu(self)

        if 0 <= section < model.columnCount():
            column = model.column_name(section)
            menu.addAction(
                "Aufsteigend sortieren",
                lambda: self.set_sort(column, False),
            )
            menu.addAction(
                "Absteigend sortieren",
                lambda: self.set_sort(column, True),
            )
            menu.addAction(
                "Filter für diese Spalte…",
                lambda: self.open_filter_dialog(column),
            )
            if any(active.column == column for active in self._filters):
                menu.addAction(
                    "Filter dieser Spalte entfernen",
                    lambda: self._remove_column_filter(column),
                )
            menu.addSeparator()
            if column in self._hidden:
                menu.addAction(
                    "Spalte einblenden",
                    lambda: self.set_column_visible(column, True),
                )
            else:
                menu.addAction(
                    "Spalte ausblenden",
                    lambda: self.set_column_visible(column, False),
                )
            menu.addSeparator()

        columns_menu = menu.addMenu("Spalten")
        for column in self._full_frame.columns:
            action = columns_menu.addAction(column)
            action.setCheckable(True)
            action.setChecked(column not in self._hidden)
            action.toggled.connect(
                lambda checked, name=column: self.set_column_visible(
                    name, checked
                )
            )

        menu.exec(header.mapToGlobal(position))

    def _remove_column_filter(self, column: str) -> None:
        remaining = [
            active for active in self._filters if active.column != column
        ]
        if len(remaining) == len(self._filters):
            return
        self._filters = remaining
        self._schedule_query()

    def closeEvent(self, event) -> None:
        self._timer.stop()
        self._search_timer.stop()
        if self._cancel_token is not None:
            self._cancel_token.set()
        if self._search_cancel is not None:
            self._search_cancel.set()
        if self._load_cancel is not None:
            self._load_cancel.set()
        self._close_progress()
        super().closeEvent(event)
