"""Kopfzeile mit Filtersymbol pro Spalte."""

from __future__ import annotations

from PyQt6.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPalette, QPolygon
from PyQt6.QtWidgets import QHeaderView

_ICON_SIZE = 16
_RIGHT_OFFSET = 26
_MIN_SECTION_WIDTH = 44


class FilterHeader(QHeaderView):
    """Zeichnet rechts in jeder Spalte ein Trichter-Symbol.

    Ein Klick auf das Symbol meldet die Spalte über `filterRequested`; alle
    anderen Klicks verhalten sich wie bei einer normalen Kopfzeile.
    """

    filterRequested = pyqtSignal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(Qt.Orientation.Horizontal, parent)
        self._filtered: set[int] = set()
        self.setSectionsClickable(True)
        self.setHighlightSections(True)
        self.setSortIndicatorShown(True)

    def set_filtered_sections(self, sections: set[int]) -> None:
        if sections == self._filtered:
            return
        self._filtered = set(sections)
        self.viewport().update()

    def icon_rect(self, section: int) -> QRect:
        left = self.sectionViewportPosition(section)
        center = left + self.sectionSize(section) - _RIGHT_OFFSET
        return QRect(center - _ICON_SIZE // 2, 0, _ICON_SIZE, self.height())

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        active = self.palette().color(QPalette.ColorRole.Highlight)
        inactive = QColor(self.palette().color(QPalette.ColorRole.Text))
        inactive.setAlpha(120)

        for section in range(self.count()):
            if self.isSectionHidden(section):
                continue
            if self.sectionSize(section) < _MIN_SECTION_WIDTH:
                continue
            rect = self.icon_rect(section)
            if rect.right() < 0 or rect.left() > self.viewport().width():
                continue
            self._draw_funnel(
                painter, rect, active if section in self._filtered else inactive
            )
        painter.end()

    @staticmethod
    def _draw_funnel(painter: QPainter, rect: QRect, color: QColor) -> None:
        center_x = rect.center().x()
        top = rect.center().y() - 5
        points = [
            QPoint(center_x - 6, top),
            QPoint(center_x + 6, top),
            QPoint(center_x + 2, top + 5),
            QPoint(center_x + 2, top + 10),
            QPoint(center_x - 2, top + 8),
            QPoint(center_x - 2, top + 5),
        ]
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawPolygon(QPolygon(points))

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            point = event.position().toPoint()
            section = self.logicalIndexAt(point)
            if (
                section >= 0
                and self.sectionSize(section) >= _MIN_SECTION_WIDTH
                and self.icon_rect(section).contains(point)
            ):
                self.filterRequested.emit(section)
                event.accept()
                return
        super().mousePressEvent(event)
