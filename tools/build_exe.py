"""Baut csv-dis als eigenständige Windows-Anwendung.

Ergebnis: `dist/csv-dis/csv-dis.exe` mit eingebettetem Programm-Icon. Das
Verzeichnis enthält zusätzlich die Laufzeitbibliotheken; es muss beim
Weitergeben vollständig kopiert werden.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "tools" / "launcher.py"
SRC = ROOT / "src"
ICON = SRC / "csv_dis" / "assets" / "csv-dis.ico"
DIST = ROOT / "dist"
WORK = ROOT / "build"
NAME = "csv-dis"
LICENSE_FILES = ("LICENSE", "THIRD-PARTY-NOTICES.md")


def build_arguments() -> list[str]:
    """Argumente für PyInstaller; ohne Seiteneffekte und damit testbar."""
    return [
        str(ENTRY),
        "--name",
        NAME,
        "--icon",
        str(ICON),
        "--windowed",
        "--noconfirm",
        "--clean",
        "--paths",
        str(SRC),
        # Das Icon wird zur Laufzeit über importlib.resources geladen.
        "--add-data",
        f"{ICON}{os.pathsep}csv_dis{os.sep}assets",
        "--distpath",
        str(DIST),
        "--workpath",
        str(WORK),
        "--specpath",
        str(WORK),
    ]


def executable() -> Path:
    return DIST / NAME / f"{NAME}.exe"


def copy_license_files() -> list[Path]:
    """Lizenztexte neben die .exe legen, damit die Weitergabe vollständig ist."""
    copied = []
    for name in LICENSE_FILES:
        destination = DIST / NAME / name
        shutil.copy2(ROOT / name, destination)
        copied.append(destination)
    return copied


def main() -> int:
    from PyInstaller.__main__ import run

    print("Baue", NAME, "…")
    run(build_arguments())
    target = executable()
    if not target.exists():
        print("Build fehlgeschlagen, nicht gefunden:", target, file=sys.stderr)
        return 1
    for path in copy_license_files():
        print("Lizenz:", path)
    print("Fertig:", target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
