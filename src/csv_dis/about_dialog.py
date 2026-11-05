"""Dialog „Über csv-dis“ mit Version, Lizenz und Laufzeitbibliotheken."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as package_version
from platform import python_version

import polars as pl
from PyQt6.QtCore import PYQT_VERSION_STR, qVersion, Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from . import __version__
from .resources import app_icon

_COPYRIGHT = "Copyright (C) 2026 Ralf Joswig"
_LICENSE = (
    "Dieses Programm steht unter der GNU General Public License v3.0 "
    "(GPLv3). Der vollständige Lizenztext liegt in der Datei LICENSE."
)
_NOTICES = (
    "Die vollständigen Drittlizenztexte stehen in THIRD-PARTY-NOTICES.md."
)


def _pyqt_version() -> str:
    try:
        return package_version("PyQt6")
    except PackageNotFoundError:
        return PYQT_VERSION_STR


def library_rows() -> list[tuple[str, str, str]]:
    """Name, installierte Version und Lizenz der Laufzeitbibliotheken."""
    return [
        ("Python", python_version(), "PSF-Lizenz"),
        ("PyQt6", _pyqt_version(), "GPL-3.0-only"),
        ("Qt", qVersion(), "LGPLv3"),
        ("Polars", pl.__version__, "MIT"),
    ]


class AboutDialog(QDialog):
    """Modaler Über-Dialog; vollständige Texte liegen neben dem Programm."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Über csv-dis")
        self.setWindowIcon(app_icon())
        self.setModal(True)
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        icon_label = QLabel(self)
        icon_label.setPixmap(app_icon().pixmap(64, 64))
        header.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)

        title_box = QVBoxLayout()
        title = QLabel(f"csv-dis {__version__}", self)
        title.setObjectName("about_version")
        title.setTextFormat(Qt.TextFormat.PlainText)
        font = title.font()
        font.setPointSize(font.pointSize() + 6)
        font.setBold(True)
        title.setFont(font)
        subtitle = QLabel("Lokaler CSV-Betrachter, read-only", self)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        title_box.addStretch(1)
        header.addLayout(title_box, 1)
        layout.addLayout(header)

        self.copyright_label = QLabel(_COPYRIGHT, self)
        self.copyright_label.setObjectName("about_copyright")
        layout.addWidget(self.copyright_label)

        self.license_label = QLabel(_LICENSE, self)
        self.license_label.setObjectName("about_license")
        self.license_label.setWordWrap(True)
        layout.addWidget(self.license_label)

        libraries_title = QLabel("Verwendete Bibliotheken", self)
        font = libraries_title.font()
        font.setBold(True)
        libraries_title.setFont(font)
        layout.addWidget(libraries_title)

        rows = library_rows()
        self.libraries = QTableWidget(len(rows), 3, self)
        self.libraries.setObjectName("about_libraries")
        self.libraries.setHorizontalHeaderLabels(
            ["Bibliothek", "Version", "Lizenz"]
        )
        self.libraries.verticalHeader().setVisible(False)
        self.libraries.setShowGrid(False)
        self.libraries.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )
        self.libraries.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        for row, values in enumerate(rows):
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.libraries.setItem(row, column, item)
        header_view = self.libraries.horizontalHeader()
        header_view.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        header_view.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.libraries.setFixedHeight(
            header_view.sizeHint().height() + len(rows) * 30 + 4
        )
        layout.addWidget(self.libraries)

        notices = QLabel(_NOTICES, self)
        notices.setWordWrap(True)
        layout.addWidget(notices)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok, parent=self
        )
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
