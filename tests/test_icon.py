from __future__ import annotations

import struct
from importlib import util
from pathlib import Path

import pytest
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QApplication

from csv_dis.resources import app_icon

_ASSET = Path(__file__).resolve().parents[1] / "src" / "csv_dis" / "assets" / "csv-dis.ico"
_SIZES = (16, 24, 32, 48, 64, 128, 256)


@pytest.fixture(scope="session")
def app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _ico_sizes(data: bytes) -> list[int]:
    reserved, kind, count = struct.unpack_from("<HHH", data, 0)
    assert reserved == 0
    assert kind == 1
    sizes: list[int] = []
    offset = 6
    for _ in range(count):
        width, height = struct.unpack_from("<BB", data, offset)
        sizes.append(width or 256)
        assert height == width
        offset += 16
    return sizes


def test_icon_file_contains_all_sizes() -> None:
    data = _ASSET.read_bytes()
    assert _ico_sizes(data) == list(_SIZES)


def test_icon_is_loadable(app: QApplication) -> None:
    icon = app_icon()
    assert icon.isNull() is False
    available = {size.width() for size in icon.availableSizes()}
    assert set(_SIZES) <= available
    assert icon.pixmap(QSize(64, 64)).isNull() is False


def test_icon_matches_generator(app: QApplication) -> None:
    spec = util.spec_from_file_location(
        "make_icon", Path(__file__).resolve().parents[1] / "tools" / "make_icon.py"
    )
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.build_icon() == _ASSET.read_bytes()
