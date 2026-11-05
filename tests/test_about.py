from __future__ import annotations

import pytest
from PyQt6.QtCore import Qt, qVersion
from PyQt6.QtWidgets import QApplication, QLabel

from csv_dis import __version__
from csv_dis.about_dialog import AboutDialog, library_rows


@pytest.fixture(scope="session")
def app() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def dialog(app: QApplication) -> AboutDialog:
    about = AboutDialog()
    yield about
    about.close()


def test_dialog_shows_name_and_version(dialog: AboutDialog) -> None:
    assert dialog.windowTitle() == "Über csv-dis"
    version_label = dialog.findChild(QLabel, "about_version")
    assert version_label is not None
    assert version_label.text() == f"csv-dis {__version__}"


def test_dialog_shows_copyright_and_license(dialog: AboutDialog) -> None:
    copyright_label = dialog.findChild(QLabel, "about_copyright")
    assert copyright_label is not None
    assert "Ralf Joswig" in copyright_label.text()

    license_label = dialog.findChild(QLabel, "about_license")
    assert license_label is not None
    assert "GPLv3" in license_label.text()
    assert "LICENSE" in license_label.text()


def test_dialog_lists_runtime_stack(dialog: AboutDialog) -> None:
    table = dialog.libraries
    rows = library_rows()
    assert table.rowCount() == len(rows) == 4
    names = [table.item(row, 0).text() for row in range(table.rowCount())]
    assert names == ["Python", "PyQt6", "Qt", "Polars"]
    for row in range(table.rowCount()):
        assert table.item(row, 1).text() != ""
        assert table.item(row, 2).text() != ""
    assert table.item(2, 1).text() == qVersion()


def test_dialog_mentions_notices_file(dialog: AboutDialog) -> None:
    texts = [label.text() for label in dialog.findChildren(QLabel)]
    assert any("THIRD-PARTY-NOTICES.md" in text for text in texts)


def test_dialog_is_modal_and_has_icon(dialog: AboutDialog) -> None:
    assert dialog.isModal() is True
    assert dialog.windowIcon().isNull() is False
