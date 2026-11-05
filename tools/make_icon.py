"""Erzeugt das Programm-Icon als ICO-Datei (ohne externe Bild bibliothek)."""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

from PyQt6.QtCore import QBuffer, QIODevice, QRectF, Qt
from PyQt6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPen, QPolygonF
from PyQt6.QtCore import QPointF

SIZES = (16, 24, 32, 48, 64, 128, 256)

_BACKGROUND = QColor("#1e3a5f")
_GRID = QColor("#1e3a5f")
_CARD = QColor("#ffffff")
_ACCENT = QColor("#f2b134")


def _render(size: int, supersample: int = 4) -> QImage:
    scale = size * supersample
    image = QImage(
        scale, scale, QImage.Format.Format_ARGB32_Premultiplied
    )
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    margin = scale * 0.06
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(_BACKGROUND)
    painter.drawRoundedRect(
        QRectF(margin, margin, scale - 2 * margin, scale - 2 * margin),
        scale * 0.16,
        scale * 0.16,
    )

    left = scale * 0.16
    top = scale * 0.18
    right = scale * 0.84
    bottom = scale * 0.60
    card = QRectF(left, top, right - left, bottom - top)
    painter.setBrush(_CARD)
    painter.drawRoundedRect(card, scale * 0.035, scale * 0.035)

    header_height = (bottom - top) * 0.26
    painter.setBrush(_ACCENT)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRect(QRectF(left, top, right - left, header_height))

    painter.setPen(QPen(_GRID, max(1.0, scale * 0.018)))
    for index in range(1, 3):
        x = left + (right - left) * index / 3
        painter.drawLine(QPointF(x, top), QPointF(x, bottom))
        y = top + header_height + (bottom - top - header_height) * index / 3
        painter.drawLine(QPointF(left, y), QPointF(right, y))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(card, scale * 0.035, scale * 0.035)

    center = scale * 0.5
    funnel_top = scale * 0.68
    width = scale * 0.36
    height = scale * 0.20
    stem = width * 0.34
    points = [
        QPointF(center - width / 2, funnel_top),
        QPointF(center + width / 2, funnel_top),
        QPointF(center + stem / 2, funnel_top + height * 0.55),
        QPointF(center + stem / 2, funnel_top + height),
        QPointF(center - stem / 2, funnel_top + height * 0.82),
        QPointF(center - stem / 2, funnel_top + height * 0.55),
    ]
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(_ACCENT)
    painter.drawPolygon(QPolygonF(points))
    painter.end()

    return image.scaled(
        size,
        size,
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def _png_bytes(image: QImage) -> bytes:
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not image.save(buffer, "PNG"):
        raise RuntimeError("PNG konnte nicht geschrieben werden")
    return bytes(buffer.data())


def _ico_bytes(images: list[tuple[int, bytes]]) -> bytes:
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    directory: list[bytes] = []
    payload: list[bytes] = []
    for size, data in images:
        dimension = 0 if size >= 256 else size
        directory.append(
            struct.pack(
                "<BBBBHHII",
                dimension,
                dimension,
                0,
                0,
                1,
                32,
                len(data),
                offset,
            )
        )
        payload.append(data)
        offset += len(data)
    return header + b"".join(directory) + b"".join(payload)


def build_icon() -> bytes:
    images = [(size, _png_bytes(_render(size))) for size in SIZES]
    return _ico_bytes(images)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "src" / "csv_dis" / "assets" / "csv-dis.ico",
    )
    parser.add_argument("--preview", type=Path, default=None)
    args = parser.parse_args(argv)

    app = QGuiApplication.instance() or QGuiApplication([])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(build_icon())
    print(f"Icon geschrieben: {args.output}")

    if args.preview is not None:
        preview = _render(256)
        preview.save(str(args.preview), "PNG")
        print(f"Vorschau: {args.preview}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
