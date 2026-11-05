from __future__ import annotations

import time
from pathlib import Path

import pytest
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox

from csv_dis import main_window as main_window_module
from csv_dis.main_window import MainWindow
from csv_dis.parser_dialog import ParserDialog
from csv_dis.query import Filter, FilterOperator


@pytest.fixture(scope="session")
def app() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def window(app: QApplication) -> MainWindow:
    window = MainWindow()
    yield window
    window.close()


def _wait_until(predicate, timeout_ms: int = 5000) -> bool:
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        if predicate():
            return True
        QTest.qWait(25)
    return predicate()


def _comma_file(path: Path) -> Path:
    path.write_text("name,preis\nApfel,1\nbirne,2\n", encoding="utf-8")
    return path


def test_parser_action_needs_a_file(window: MainWindow, tmp_path: Path) -> None:
    assert window._parser_action.isEnabled() is False
    assert window.load_path(_comma_file(tmp_path / "a.csv")) is True
    assert window._parser_action.isEnabled() is True


def test_dialog_prefills_current_values(
    window: MainWindow, tmp_path: Path
) -> None:
    path = tmp_path / "a.csv"
    path.write_text("a;b\n1;2\n", encoding="utf-8")
    assert window.load_path(path) is True

    dialog = ParserDialog(path, window._delimiter, window._encoding, window)
    assert dialog.chosen_delimiter() == ";"
    assert dialog.chosen_encoding() == "utf-8"

    dialog.delimiter_combo.setCurrentIndex(
        dialog.delimiter_combo.findData(",")
    )
    dialog.encoding_combo.setCurrentIndex(
        dialog.encoding_combo.findData("cp1252")
    )
    assert dialog.chosen_delimiter() == ","
    assert dialog.chosen_encoding() == "cp1252"


def test_forced_delimiter_reloads_and_resets_filters(
    window: MainWindow, tmp_path: Path
) -> None:
    path = _comma_file(tmp_path / "a.csv")
    assert window.load_path(path) is True
    assert window.table.model().columnCount() == 2

    window.set_filter(Filter("name", FilterOperator.CONTAINS, "Apf"))
    window.apply_now()
    assert "1 von 2 Zeilen" in window.statusBar().currentMessage()

    assert window.load_path(path, delimiter=";") is True
    model = window.table.model()
    assert model.columnCount() == 1
    assert model.data(model.index(0, 0)) == "Apfel,1"
    assert "Trennzeichen ;" in window.statusBar().currentMessage()
    assert "2 von 2 Zeilen" in window.statusBar().currentMessage()
    assert window.filter_bar.isHidden() is True
    assert window._delimiter == ";"

    assert window.load_path(path, delimiter=",", encoding="utf-8") is True
    assert window.table.model().columnCount() == 2
    assert window._encoding == "utf-8"


def test_forced_delimiter_through_worker(
    window: MainWindow, tmp_path: Path
) -> None:
    path = _comma_file(tmp_path / "a.csv")
    window.open_path(path, delimiter=";", encoding="utf-8")

    assert _wait_until(lambda: window.table.model() is not None)
    assert window.table.model().columnCount() == 1
    assert "Trennzeichen ;" in window.statusBar().currentMessage()


def test_failed_encoding_keeps_previous_view(
    window: MainWindow,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "cp1252.csv"
    path.write_bytes("name;ort\nMüller;Köln\n".encode("cp1252"))
    assert window.load_path(path, encoding="cp1252") is True
    assert window._encoding == "cp1252"
    assert window.table.model().columnCount() == 2

    messages: list[str] = []
    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda _parent, _title, text: messages.append(text),
    )

    assert window.load_path(path, encoding="utf-8") is False
    assert messages
    assert window._encoding == "cp1252"
    assert window.table.model().columnCount() == 2


def test_correct_parser_uses_dialog_choice(
    window: MainWindow,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _comma_file(tmp_path / "a.csv")
    assert window.load_path(path) is True
    captured: list[tuple[Path, str, str]] = []

    class FakeDialog:
        def __init__(self, dialog_path, delimiter, encoding, parent):
            captured.append((dialog_path, delimiter, encoding))

        def exec(self):
            return QDialog.DialogCode.Accepted

        def chosen_delimiter(self):
            return ";"

        def chosen_encoding(self):
            return "utf-8"

    monkeypatch.setattr(main_window_module, "ParserDialog", FakeDialog)
    window.correct_parser()

    assert captured == [(path, ",", "utf-8")]
    assert _wait_until(lambda: window.table.model().columnCount() == 1)
    assert window._delimiter == ";"
