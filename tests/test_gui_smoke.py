from __future__ import annotations

import time
from pathlib import Path

import pytest
from PyQt6.QtCore import QMimeData, QPoint, QPointF, Qt, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from csv_dis.main_window import MainWindow


def _wait_for_model(window: MainWindow, timeout_ms: int = 5000) -> None:
    deadline = time.monotonic() + timeout_ms / 1000
    while window.table.model() is None and time.monotonic() < deadline:
        QTest.qWait(25)


@pytest.fixture(scope="session")
def app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _mime(paths: list[Path]) -> QMimeData:
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(path)) for path in paths])
    return mime


def _drag_enter(window: MainWindow, mime: QMimeData) -> QDragEnterEvent:
    event = QDragEnterEvent(
        QPoint(5, 5),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    window.dragEnterEvent(event)
    return event


def _drop(window: MainWindow, mime: QMimeData) -> QDropEvent:
    event = QDropEvent(
        QPointF(5, 5),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    window.dropEvent(event)
    return event


def _csv(path: Path, first: str) -> Path:
    path.write_text(f"a;b\n{first};2\n", encoding="utf-8")
    return path


def test_window_loads_file(app: QApplication, tmp_path: Path) -> None:
    path = _csv(tmp_path / "a.csv", "1")

    window = MainWindow()
    assert window.load_path(path) is True
    model = window.table.model()
    assert model.rowCount() == 1
    assert model.columnCount() == 2
    assert model.data(model.index(0, 0)) == "1"
    window.close()


def test_drag_and_drop_opens_file(app: QApplication, tmp_path: Path) -> None:
    path = _csv(tmp_path / "drop.csv", "1")
    mime = _mime([path])

    window = MainWindow()
    assert _drag_enter(window, mime).isAccepted() is True
    assert _drop(window, mime).isAccepted() is True
    _wait_for_model(window)
    assert window.table.model().data(window.table.model().index(0, 0)) == "1"
    window.close()


def test_drag_rejects_remote_url(app: QApplication) -> None:
    mime = QMimeData()
    mime.setUrls([QUrl("https://example.com/a.csv")])

    window = MainWindow()
    assert _drag_enter(window, mime).isAccepted() is False
    window.close()


def test_drag_rejects_directory(app: QApplication, tmp_path: Path) -> None:
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(tmp_path))])

    window = MainWindow()
    assert _drag_enter(window, mime).isAccepted() is False
    window.close()


def test_drop_opens_first_of_multiple_files(
    app: QApplication, tmp_path: Path
) -> None:
    first = _csv(tmp_path / "first.csv", "1")
    second = _csv(tmp_path / "second.csv", "9")
    mime = _mime([first, second])

    window = MainWindow()
    assert _drag_enter(window, mime).isAccepted() is True
    _drop(window, mime)
    _wait_for_model(window)
    model = window.table.model()
    assert model.data(model.index(0, 0)) == "1"
    assert "weitere" in window.statusBar().currentMessage()
    window.close()
