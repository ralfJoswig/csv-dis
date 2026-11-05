from __future__ import annotations

from pathlib import Path

import pytest
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QPushButton

from csv_dis.column_types import ColumnType
from csv_dis.filter_dialog import FilterDialog
from csv_dis.main_window import MainWindow
from csv_dis.query import Filter, FilterOperator


@pytest.fixture(scope="session")
def app() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def window(app: QApplication, tmp_path: Path) -> MainWindow:
    path = tmp_path / "daten.csv"
    path.write_text(
        "name;preis;datum\n"
        "Apfel;1.5;2024-01-01\n"
        "birne;2;2024-01-02 10:00\n"
        "Äpfel;10;2024-01-03\n"
        ";3;2024-01-04\n",
        encoding="utf-8",
    )
    window = MainWindow()
    assert window.load_path(path) is True
    yield window
    window.close()


def _rows(window: MainWindow) -> list[str]:
    model = window.table.model()
    return [model.data(model.index(row, 0)) for row in range(model.rowCount())]


def test_status_and_detected_types(window: MainWindow) -> None:
    assert "4 von 4 Zeilen" in window.statusBar().currentMessage()
    model = window.table.model()
    tooltip = model.headerData(
        1, Qt.Orientation.Horizontal, Qt.ItemDataRole.ToolTipRole
    )
    assert "Zahl" in tooltip
    tooltip = model.headerData(
        2, Qt.Orientation.Horizontal, Qt.ItemDataRole.ToolTipRole
    )
    assert "Datum" in tooltip


def test_filter_updates_rows_and_status(window: MainWindow) -> None:
    window.set_filter(Filter("name", FilterOperator.CONTAINS, "ÄPF"))
    window.apply_now()

    assert _rows(window) == ["Äpfel"]
    assert "1 von 4 Zeilen" in window.statusBar().currentMessage()

    model = window.table.model()
    header = model.headerData(
        0, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole
    )
    assert "▾" in header


def test_filter_chips_remove_individually_and_all(window: MainWindow) -> None:
    window.set_filter(Filter("name", FilterOperator.CONTAINS, "apf"))
    window.set_filter(Filter("preis", FilterOperator.GREATER, "1"))
    window.apply_now()

    chips = window.filter_bar.findChildren(QPushButton, "filter_chip")
    assert len(chips) == 2
    assert window.filter_bar.isHidden() is False
    assert _rows(window) == ["Apfel"]

    chips[0].click()
    window.apply_now()
    assert _rows(window) == ["Apfel", "birne", "Äpfel", ""]

    remove_all = window.filter_bar.findChild(
        QPushButton, "remove_all_filters"
    )
    assert remove_all is not None
    remove_all.click()
    window.apply_now()

    assert _rows(window) == ["Apfel", "birne", "Äpfel", ""]
    assert window.filter_bar.isHidden() is True
    assert "4 von 4 Zeilen" in window.statusBar().currentMessage()


def test_sorting_toggles_and_puts_empty_last(window: MainWindow) -> None:
    window.toggle_sort("preis")
    window.apply_now()
    assert [row for row in _rows(window)] == ["Apfel", "birne", "", "Äpfel"]

    window.toggle_sort("preis")
    window.apply_now()
    assert _rows(window) == ["Äpfel", "", "birne", "Apfel"]

    header = window.table.horizontalHeader()
    assert header.isSortIndicatorShown() is True
    assert header.sortIndicatorSection() == 1


def test_header_click_sorts_through_worker(window: MainWindow) -> None:
    window._header_clicked(2)
    QTest.qWait(600)
    assert _rows(window) == ["Apfel", "birne", "Äpfel", ""]


def test_hide_and_show_columns(window: MainWindow) -> None:
    window.set_column_visible("datum", False)
    assert window.table.isColumnHidden(2) is True

    for column in ("name", "preis", "datum"):
        window.set_column_visible(column, False)
    assert "Alle Spalten sind ausgeblendet" in window.statusBar().currentMessage()

    window.show_all_columns()
    assert window.table.isColumnHidden(0) is False
    assert window.table.isColumnHidden(2) is False
    assert "ausgeblendet" not in window.statusBar().currentMessage()


def test_live_filter_runs_after_delay(window: MainWindow) -> None:
    window.set_filter(Filter("preis", FilterOperator.LESS, "2"))
    QTest.qWait(600)
    assert _rows(window) == ["Apfel"]


def test_filter_icon_opens_dialog(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    window.resize(900, 400)
    window.show()
    QTest.qWait(20)

    opened: list[str] = []
    monkeypatch.setattr(window, "open_filter_dialog", opened.append)

    header = window.table.horizontalHeader()
    position = header.icon_rect(1).center()
    QTest.mouseClick(
        header.viewport(), Qt.MouseButton.LeftButton, pos=QPoint(position)
    )

    assert opened == ["preis"]
    assert window._sort is None


def test_dialog_remove_button_clears_filter(window: MainWindow) -> None:
    current = Filter("preis", FilterOperator.EQUALS, "2")
    dialog = FilterDialog("preis", ColumnType.NUMBER, current, window)
    assert dialog.operator_combo.currentData() is FilterOperator.EQUALS
    assert dialog.value_edit.text() == "2"
    dialog.remove_button.click()
    assert dialog.result_filter() is None


def test_dialog_rejects_invalid_number(window: MainWindow) -> None:
    dialog = FilterDialog("preis", ColumnType.NUMBER, parent=window)
    dialog.value_edit.setText("zehn")
    dialog.accept()

    assert dialog.result_filter() is None
    assert dialog.error_label.text() != ""

    dialog.value_edit.setText("2")
    dialog.accept()
    assert dialog.result_filter() == Filter(
        "preis", FilterOperator.EQUALS, "2"
    )
