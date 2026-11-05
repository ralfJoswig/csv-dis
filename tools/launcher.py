"""Einstiegsskript für den PyInstaller-Build.

PyInstaller führt sein Startskript als eigenständiges Programm aus; relative
Importe aus `csv_dis.__main__` funktionieren dort nicht. Dieses Skript
importiert deshalb absolut und wird nur beim Build verwendet.
"""

from __future__ import annotations

from csv_dis.app import main

if __name__ == "__main__":
    raise SystemExit(main())
