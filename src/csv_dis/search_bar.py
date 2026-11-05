"""Dauerhafte Suchleiste über der Tabelle."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)


class SearchLineEdit(QLineEdit):
    """Suchfeld mit Enter (weiter), Umschalt+Enter (zurück) und Esc (leeren)."""

    nextRequested = pyqtSignal()
    previousRequested = pyqtSignal()
    escapePressed = pyqtSignal()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.previousRequested.emit()
            else:
                self.nextRequested.emit()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Escape:
            self.clear()
            self.escapePressed.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class SearchBar(QWidget):
    """Suchfeld, Trefferzähler und Navigation; immer sichtbar."""

    textChanged = pyqtSignal(str)
    nextRequested = pyqtSignal()
    previousRequested = pyqtSignal()
    escapePressed = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("search_bar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(6)

        label = QLabel("Suche:", self)
        layout.addWidget(label)

        self.edit = SearchLineEdit(self)
        self.edit.setObjectName("search_edit")
        self.edit.setPlaceholderText("Sichtbare Spalten durchsuchen…")
        self.edit.setClearButtonEnabled(True)
        layout.addWidget(self.edit, 1)

        self.counter = QLabel(self)
        self.counter.setObjectName("search_counter")
        self.counter.setMinimumWidth(140)
        layout.addWidget(self.counter)

        self.previous_button = QPushButton("Zurück", self)
        self.previous_button.setObjectName("search_previous")
        self.previous_button.setEnabled(False)
        layout.addWidget(self.previous_button)

        self.next_button = QPushButton("Weiter", self)
        self.next_button.setObjectName("search_next")
        self.next_button.setEnabled(False)
        layout.addWidget(self.next_button)

        self.edit.textChanged.connect(self.textChanged)
        self.edit.nextRequested.connect(self.nextRequested)
        self.edit.previousRequested.connect(self.previousRequested)
        self.edit.escapePressed.connect(self.escapePressed)
        self.previous_button.clicked.connect(self.previousRequested)
        self.next_button.clicked.connect(self.nextRequested)

    def focus_edit(self) -> None:
        self.edit.setFocus()
        self.edit.selectAll()

    def set_counter(self, text: str) -> None:
        self.counter.setText(text)

    def set_navigation_enabled(self, enabled: bool) -> None:
        self.previous_button.setEnabled(enabled)
        self.next_button.setEnabled(enabled)
