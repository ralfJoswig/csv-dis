"""Erzeugt eine große CSV-Testdatei für die Abnahme."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path


def build_row(row: int, columns: int) -> list[str]:
    values = [
        f"zeile {row}",
        str(row % 1000),
        f"{row % 100}.{row % 100:02d}",
        f"2026-10-{(row % 28) + 1:02d}",
        f"Text äöü {row}",
    ]
    if columns <= len(values):
        return values[:columns]
    return values + [f"wert {index} {row}" for index in range(len(values), columns)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(tempfile.gettempdir()) / "csv-dis-large.csv",
        help="Zielpfad (Standard: temporäres Verzeichnis)",
    )
    parser.add_argument("--rows", type=int, default=1_000_000)
    parser.add_argument("--columns", type=int, default=5)
    args = parser.parse_args()
    if args.rows < 1 or args.columns < 1:
        parser.error("--rows und --columns müssen positiv sein")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        handle.write(
            ";".join(f"spalte_{index + 1}" for index in range(args.columns)) + "\n"
        )
        for row in range(args.rows):
            handle.write(";".join(build_row(row, args.columns)) + "\n")

    print(f"{args.rows} Zeilen, {args.columns} Spalten: {args.output}")
    print(f"Größe: {args.output.stat().st_size / 1024 / 1024:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
