from __future__ import annotations

from pathlib import Path

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from csv_dis.main_window import MainWindow
from csv_dis.query import Filter, FilterOperator


@pytest.fixture(scope="session")
def app() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def window(app: QApplication, tmp_path: Path) -> MainWindow:
    path = tmp_path / "daten.csv"
    path.write_text(
        "name;ort;preis\n"
        "Apfel;Berlin;1\n"
        "Birne;München;2\n"
        "Äpfel;Berlin;3\n",
        encoding="utf-8",
    )
    window = MainWindow()
    window.show()
    assert window.load_path(path) is True
    yield window
    window.close()


def _background(window: MainWindow, row: int, column: int) -> QBrush | None:
    model = window.table.model()
    return model.data(model.index(row, column), Qt.ItemDataRole.BackgroundRole)


def _settle() -> None:
    QTest.qWait(700)


def test_search_bar_is_present_and_enabled(window: MainWindow) -> None:
    assert window.search_bar.isHidden() is False
    assert window.search_bar.isEnabled() is True
    assert window.search_bar.edit.placeholderText() == (
        "Sichtbare Spalten durchsuchen…"
    )


def test_search_bar_is_disabled_without_file(app: QApplication) -> None:
    window = MainWindow()
    assert window.search_bar.isEnabled() is False
    window.close()


def test_search_marks_cells_and_counts(window: MainWindow) -> None:
    window.search_bar.edit.setText("berlin")
    _settle()

    assert window.search_bar.counter.text() == "1 von 2 Treffern"
    assert window.search_bar.next_button.isEnabled() is True
    assert _background(window, 0, 1) is not None
    assert _background(window, 2, 1) is not None
    assert _background(window, 1, 1) is None
    assert _background(window, 0, 0) is None


def test_current_hit_is_stronger(window: MainWindow) -> None:
    window.search_bar.edit.setText("berlin")
    _settle()

    first = _background(window, 0, 1)
    second = _background(window, 2, 1)
    assert first is not None and second is not None
    assert first.color() != second.color()


def test_hit_text_stays_readable(window: MainWindow) -> None:
    window.search_bar.edit.setText("berlin")
    _settle()

    model = window.table.model()
    foreground = model.data(
        model.index(0, 1), Qt.ItemDataRole.ForegroundRole
    )
    assert foreground is not None
    assert foreground.color().lightness() < 100
    assert model.data(
        model.index(1, 1), Qt.ItemDataRole.ForegroundRole
    ) is None


def test_terms_may_span_columns(window: MainWindow) -> None:
    window.search_bar.edit.setText("apfel berlin")
    _settle()
    assert window.search_bar.counter.text() == "1 von 1 Treffern"

    window.search_bar.edit.setText("äpfel berlin")
    _settle()
    assert window.search_bar.counter.text() == "1 von 1 Treffern"
    assert _background(window, 2, 0) is not None


def test_navigation_wraps(window: MainWindow) -> None:
    window.search_bar.edit.setText("berlin")
    _settle()
    assert window.search_bar.counter.text() == "1 von 2 Treffern"

    window.next_hit()
    assert window.search_bar.counter.text() == "2 von 2 Treffern"
    window.next_hit()
    assert window.search_bar.counter.text() == "1 von 2 Treffern"
    window.previous_hit()
    assert window.search_bar.counter.text() == "2 von 2 Treffern"


def test_buttons_navigate(window: MainWindow) -> None:
    window.search_bar.edit.setText("berlin")
    _settle()
    assert window.search_bar.counter.text() == "1 von 2 Treffern"

    window.search_bar.next_button.click()
    assert window.search_bar.counter.text() == "2 von 2 Treffern"

    window.search_bar.previous_button.click()
    assert window.search_bar.counter.text() == "1 von 2 Treffern"


def test_enter_and_shift_enter_navigate(window: MainWindow) -> None:
    window.search_bar.edit.setText("berlin")
    _settle()
    window.search_bar.edit.setFocus()

    QTest.keyClick(window.search_bar.edit, Qt.Key.Key_Return)
    assert window.search_bar.counter.text() == "2 von 2 Treffern"

    QTest.keyClick(
        window.search_bar.edit,
        Qt.Key.Key_Return,
        Qt.KeyboardModifier.ShiftModifier,
    )
    assert window.search_bar.counter.text() == "1 von 2 Treffern"


def test_escape_clears_search(window: MainWindow) -> None:
    window.search_bar.edit.setText("berlin")
    _settle()
    window.search_bar.edit.setFocus()

    QTest.keyClick(window.search_bar.edit, Qt.Key.Key_Escape)

    assert window.search_bar.edit.text() == ""
    assert window.search_bar.counter.text() == ""
    assert _background(window, 0, 1) is None


def test_empty_input_shows_nothing(window: MainWindow) -> None:
    window.search_bar.edit.setText("   ")
    _settle()
    assert window.search_bar.counter.text() == ""


def test_new_input_clears_marks_immediately(window: MainWindow) -> None:
    window.search_bar.edit.setText("berlin")
    _settle()
    assert _background(window, 0, 1) is not None

    window.search_bar.edit.setText("münchen")
    assert window.search_bar.counter.text() == "Suche…"
    assert _background(window, 0, 1) is None
    assert _background(window, 2, 1) is None


def test_filter_change_keeps_search(window: MainWindow) -> None:
    window.search_bar.edit.setText("berlin")
    _settle()

    window.set_filter(Filter("preis", FilterOperator.GREATER, "1"))
    window.apply_now()
    _settle()

    assert window.search_bar.edit.text() == "berlin"
    assert window.search_bar.counter.text() == "1 von 1 Treffern"
    model = window.table.model()
    assert model.rowCount() == 2


def test_sort_change_keeps_search(window: MainWindow) -> None:
    window.search_bar.edit.setText("berlin")
    _settle()
    assert window.search_bar.counter.text() == "1 von 2 Treffern"

    window.toggle_sort("name")
    window.apply_now()
    _settle()

    assert window.search_bar.edit.text() == "berlin"
    assert window.search_bar.counter.text() == "1 von 2 Treffern"


def test_hiding_a_column_removes_its_hits(window: MainWindow) -> None:
    window.search_bar.edit.setText("berlin")
    _settle()
    assert window.search_bar.counter.text() == "1 von 2 Treffern"

    window.set_column_visible("ort", False)
    _settle()
    assert window.search_bar.counter.text() == "0 Treffer"

    window.show_all_columns()
    _settle()
    assert window.search_bar.counter.text() == "1 von 2 Treffern"


def test_new_file_clears_search(window: MainWindow, tmp_path: Path) -> None:
    window.search_bar.edit.setText("berlin")
    _settle()

    other = tmp_path / "andere.csv"
    other.write_text("a;b\n1;2\n", encoding="utf-8")
    assert window.load_path(other) is True

    assert window.search_bar.edit.text() == ""
    assert window.search_bar.counter.text() == ""


def test_find_action_focuses_search(window: MainWindow) -> None:
    assert "Ctrl+F" in window._find_action.shortcut().toString()
    window.activateWindow()
    QTest.qWait(50)
    window._find_action.trigger()
    QTest.qWait(50)
    assert window.search_bar.edit.hasFocus() is True


def test_ctrl_f_focuses_search(window: MainWindow) -> None:
    window.table.setFocus()
    window.activateWindow()
    QTest.qWait(50)

    QTest.keyClick(
        window, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier
    )
    QTest.qWait(50)

    assert window.search_bar.edit.hasFocus() is True
