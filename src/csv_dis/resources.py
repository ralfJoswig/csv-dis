"""Zugriff auf mitgelieferte Ressourcen."""

from __future__ import annotations

from functools import lru_cache
from importlib import resources

from PyQt6.QtGui import QIcon


@lru_cache(maxsize=1)
def app_icon() -> QIcon:
    """Lädt das Programm-Icon aus dem Paket."""
    resource = resources.files("csv_dis").joinpath("assets/csv-dis.ico")
    with resources.as_file(resource) as path:
        return QIcon(str(path))
