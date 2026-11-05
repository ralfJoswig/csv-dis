from __future__ import annotations

import time
from pathlib import Path

import pytest
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

import csv_dis.app as app_module
from csv_dis.splash import SPLASH_MIN_MS


@pytest.fixture(scope="session")
def app() -> QApplication:
    return QApplication.instance() or QApplication([])


class _AppProxy:
    """Delegiert an die vorhandene QApplication und beendet die Schleife."""

    def __init__(self, real: QApplication) -> None:
        self._real = real

    def setApplicationName(self, name: str) -> None:
        self._real.setApplicationName(name)

    def setApplicationDisplayName(self, name: str) -> None:
        self._real.setApplicationDisplayName(name)

    def setApplicationVersion(self, version: str) -> None:
        self._real.setApplicationVersion(version)

    def setWindowIcon(self, icon) -> None:
        self._real.setWindowIcon(icon)

    def processEvents(self) -> None:
        self._real.processEvents()

    def exec(self) -> int:
        QTest.qWait(SPLASH_MIN_MS + 500)
        return 0


def test_startup_waits_for_splash_before_opening_file(
    app: QApplication, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "daten.csv"
    path.write_text("a;b\n1;2\n", encoding="utf-8")
    events: list[tuple[str, float]] = []
    start = time.monotonic()

    class FakeSplash:
        def __init__(self, version: str) -> None:
            self.version = version
            events.append(("splash.new", time.monotonic() - start))

        def show(self) -> None:
            events.append(("splash.show", time.monotonic() - start))

        def finish(self, window) -> None:
            events.append(("splash.finish", time.monotonic() - start))

        def deleteLater(self) -> None:
            events.append(("splash.delete", time.monotonic() - start))

    class FakeWindow:
        def __init__(self) -> None:
            events.append(("window.new", time.monotonic() - start))

        def show(self) -> None:
            events.append(("window.show", time.monotonic() - start))

        def open_path(self, opened: Path) -> None:
            events.append((f"open:{opened.name}", time.monotonic() - start))

    monkeypatch.setattr(
        app_module, "create_splash", lambda version: FakeSplash(version)
    )
    monkeypatch.setattr(app_module, "MainWindow", FakeWindow)
    monkeypatch.setattr(app_module, "QApplication", lambda args: _AppProxy(app))

    assert app_module.main(["csv-dis", str(path)]) == 0

    assert app.windowIcon().isNull() is False
    assert app.applicationVersion() == "1.1.0"

    names = [name for name, _ in events]
    assert names == [
        "splash.new",
        "splash.show",
        "window.new",
        "window.show",
        "splash.finish",
        "splash.delete",
        "open:daten.csv",
    ]
    finish_time = dict(events)["splash.finish"]
    open_time = dict(events)["open:daten.csv"]
    assert finish_time >= SPLASH_MIN_MS / 1000 - 0.1
    assert open_time >= finish_time
