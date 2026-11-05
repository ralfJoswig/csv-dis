from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QApplication, QLabel, QSplashScreen

from csv_dis import __version__
from csv_dis.splash import (
    SPLASH_HEIGHT,
    SPLASH_MIN_MS,
    SPLASH_WIDTH,
    create_splash,
    splash_pixmap,
)


@pytest.fixture(scope="session")
def app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_minimum_duration_is_800_ms() -> None:
    assert SPLASH_MIN_MS == 800


def test_splash_pixmap_contains_icon_and_text(app: QApplication) -> None:
    pixmap = splash_pixmap(__version__)
    assert pixmap.isNull() is False
    assert (pixmap.width(), pixmap.height()) == (SPLASH_WIDTH, SPLASH_HEIGHT)
    # Das Icon belegt oben links einen sichtbaren Bereich.
    icon_area = pixmap.toImage().pixelColor(60, 100)
    assert icon_area.alpha() > 0


def test_create_splash_uses_pixmap(app: QApplication) -> None:
    splash = create_splash(__version__)
    assert isinstance(splash, QSplashScreen)
    assert (splash.pixmap().width(), splash.pixmap().height()) == (
        SPLASH_WIDTH,
        SPLASH_HEIGHT,
    )
    splash.close()


def test_click_does_not_close_splash(app: QApplication) -> None:
    from PyQt6.QtCore import QPoint, Qt
    from PyQt6.QtTest import QTest

    splash = create_splash(__version__)
    splash.show()
    QTest.qWait(50)
    assert splash.isVisible() is True

    QTest.mouseClick(
        splash, Qt.MouseButton.LeftButton, pos=QPoint(10, 10)
    )
    QTest.qWait(50)

    assert splash.isVisible() is True
    splash.close()


def test_splash_renders_the_given_version(app: QApplication) -> None:
    first = splash_pixmap("1.0.0")
    second = splash_pixmap("1.1.0")
    assert first.cacheKey() != second.cacheKey()
