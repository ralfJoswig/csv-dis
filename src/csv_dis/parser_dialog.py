"""Dialog zum Korrigieren von Trennzeichen und Encoding."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
)

from .csv_loader import (
    SUPPORTED_DELIMITERS,
    SUPPORTED_ENCODINGS,
    EncodingInfo,
    delimiter_label,
    encoding_label,
)


class ParserDialog(QDialog):
    """Lädt die aktuelle Datei mit manuell gewähltem Trennzeichen/Encoding neu."""

    def __init__(
        self,
        path: Path,
        delimiter: str,
        encoding: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Trennzeichen und Encoding")
        self.setModal(True)

        title = QLabel(f"<b>{path.name}</b>")
        hint = QLabel(
            "Nach dem Neuladen werden Filter, Sortierung und ausgeblendete "
            "Spalten zurückgesetzt."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: palette(mid);")

        self.delimiter_combo = QComboBox()
        self.delimiter_combo.setObjectName("delimiter_combo")
        for value in SUPPORTED_DELIMITERS:
            self.delimiter_combo.addItem(delimiter_label(value), value)
        self.delimiter_combo.setCurrentIndex(
            max(0, self.delimiter_combo.findData(delimiter))
        )

        self.encoding_combo = QComboBox()
        self.encoding_combo.setObjectName("encoding_combo")
        for value in SUPPORTED_ENCODINGS:
            self.encoding_combo.addItem(
                encoding_label(EncodingInfo(value)), value
            )
        self.encoding_combo.setCurrentIndex(
            max(0, self.encoding_combo.findData(encoding))
        )

        form = QFormLayout()
        form.addRow("Trennzeichen", self.delimiter_combo)
        form.addRow("Encoding", self.encoding_combo)

        buttons = QDialogButtonBox()
        reload_button = buttons.addButton(
            "Neu laden", QDialogButtonBox.ButtonRole.AcceptRole
        )
        reload_button.setDefault(True)
        buttons.addButton("Abbrechen", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addLayout(form)
        layout.addWidget(hint)
        layout.addWidget(buttons)

    def chosen_delimiter(self) -> str:
        return self.delimiter_combo.currentData()

    def chosen_encoding(self) -> str:
        return self.encoding_combo.currentData()
