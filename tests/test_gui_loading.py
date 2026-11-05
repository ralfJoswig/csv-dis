from __future__ import annotations

import time
from pathlib import Path

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QMessageBox

from csv_dis.main_window import MainWindow


@pytest.fixture(scope="session")
def app() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def window(app: QApplication) -> MainWindow:
    window = MainWindow()
    window.show()
    yield window
    window.close()


def _csv(path: Path, first: str) -> Path:
    path.write_text(f"a;b\n{first};2\n", encoding="utf-8")
    return path


def _wait_until(predicate, timeout_ms: int = 5000) -> bool:
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        if predicate():
            return True
        QTest.qWait(25)
    return predicate()


def test_open_path_loads_in_background(
    window: MainWindow, tmp_path: Path
) -> None:
    path = _csv(tmp_path / "a.csv", "1")

    window.open_path(path)

    assert window._progress is not None
    assert window._progress.isHidden() is False
    assert (
        window._progress.windowModality()
        is Qt.WindowModality.NonModal
    )
    assert window.table.model() is None

    assert _wait_until(lambda: window.table.model() is not None)
    assert window.table.model().rowCount() == 1
    assert window.table.model().data(window.table.model().index(0, 0)) == "1"
    assert window._progress is None
    assert "1 von 1 Zeilen" in window.statusBar().currentMessage()
    assert "a.csv" in window.windowTitle()


def test_second_open_replaces_first(
    window: MainWindow, tmp_path: Path
) -> None:
    first = _csv(tmp_path / "first.csv", "1")
    second = _csv(tmp_path / "second.csv", "9")

    window.open_path(first)
    window.open_path(second)

    assert _wait_until(lambda: window.table.model() is not None)
    assert _wait_until(lambda: "second.csv" in window.windowTitle())
    model = window.table.model()
    assert model.data(model.index(0, 0)) == "9"
    assert window._progress is None


def test_open_path_does_not_block_gui(
    window: MainWindow,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from csv_dis import main_window as main_window_module

    real_load = main_window_module.load_csv

    def slow_load(path, **kwargs):
        time.sleep(0.3)
        return real_load(path, **kwargs)

    monkeypatch.setattr(main_window_module, "load_csv", slow_load)
    path = _csv(tmp_path / "slow.csv", "1")

    started = time.monotonic()
    window.open_path(path)
    assert time.monotonic() - started < 0.2

    QTest.qWait(100)
    assert window._progress is not None
    assert window.table.model() is None

    assert _wait_until(lambda: window.table.model() is not None)
    assert window._progress is None


def test_cancel_during_load_keeps_current_view(
    window: MainWindow,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from csv_dis import main_window as main_window_module

    real_load = main_window_module.load_csv

    def slow_load(path, **kwargs):
        time.sleep(0.3)
        return real_load(path, **kwargs)

    monkeypatch.setattr(main_window_module, "load_csv", slow_load)
    path = _csv(tmp_path / "cancel.csv", "1")

    window.open_path(path)
    QTest.qWait(100)
    assert window._progress is not None
    window._progress.canceled.emit()

    assert window._progress is None
    QTest.qWait(500)
    assert window.table.model() is None
    assert "Keine Datei geöffnet" in window.statusBar().currentMessage()


def test_open_path_reports_error(
    window: MainWindow,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    messages: list[str] = []

    def fake_critical(_parent, _title, text):
        messages.append(text)

    monkeypatch.setattr(QMessageBox, "critical", fake_critical)
    window.open_path(tmp_path / "fehlt.csv")

    assert _wait_until(lambda: bool(messages))
    assert "nicht gefunden" in messages[0]
    assert window._progress is None
    assert window.table.model() is None
