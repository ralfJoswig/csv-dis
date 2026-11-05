"""Splash-Screen für den Programmstart."""

from __future__ import annotations

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor, QPainter, QPixmap
from PyQt6.QtWidgets import QSplashScreen

from .resources import app_icon

SPLASH_MIN_MS = 800
SPLASH_WIDTH = 420
SPLASH_HEIGHT = 230


def splash_pixmap(version: str) -> QPixmap:
    """Zeichnet Icon, Name und Version auf ein Splash-Bild."""
    pixmap = QPixmap(SPLASH_WIDTH, SPLASH_HEIGHT)
    pixmap.fill(QColor("#1f3a5f"))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    painter.drawPixmap(28, 64, app_icon().pixmap(96, 96))

    painter.setPen(QColor("#ffffff"))
    font = painter.font()
    font.setPointSize(24)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(
        QRect(146, 66, 250, 40),
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        "csv-dis",
    )

    font.setPointSize(11)
    font.setBold(False)
    painter.setFont(font)
    painter.setPen(QColor("#d7e3f4"))
    painter.drawText(
        QRect(148, 108, 250, 24),
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        f"Version {version}",
    )

    font.setPointSize(9)
    painter.setFont(font)
    painter.drawText(
        QRect(148, 134, 250, 24),
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        "CSV-Dateien ansehen",
    )

    painter.setPen(QColor("#f2b134"))
    painter.drawLine(28, 190, SPLASH_WIDTH - 28, 190)
    painter.end()
    return pixmap


class SplashScreen(QSplashScreen):
    """Splash, der Klicks ignoriert und nur über `finish()` verschwindet."""

    def mousePressEvent(self, event) -> None:
        event.ignore()


def create_splash(version: str) -> QSplashScreen:
    return SplashScreen(splash_pixmap(version))
