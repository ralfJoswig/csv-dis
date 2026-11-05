"""CSV-Dateien einlesen: Kodierung, Trennzeichen, Kopfzeilen und Randfälle."""

from __future__ import annotations

import codecs
import csv
import io
import os
import re
import tempfile
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import polars as pl

SUPPORTED_DELIMITERS = (";", ",", "\t", "|")
SUPPORTED_ENCODINGS = ("utf-8", "utf-8-sig", "cp1252")

_SAMPLE_BYTES = 256 * 1024
_SNIFF_ROWS = 50
_DUPLICATED = re.compile(r"^(.*)_duplicated_(\d+)$")


class CsvLoadError(Exception):
    """Fehler, der dem Benutzer im Dialog angezeigt werden kann."""


@dataclass(frozen=True)
class EncodingInfo:
    encoding: str
    fallback: bool = False
    bom: bool = False


@dataclass(frozen=True)
class LoadResult:
    frame: pl.DataFrame
    delimiter: str
    encoding: EncodingInfo
    warnings: tuple[str, ...] = ()


def detect_encoding(path: Path) -> EncodingInfo:
    """Erkennt UTF-8 (mit oder ohne BOM) und fällt sonst auf Windows-1252 zurück."""
    with path.open("rb") as handle:
        start = handle.read(3)
        handle.seek(0)
        has_bom = start == codecs.BOM_UTF8
        decoder = codecs.getincrementaldecoder("utf-8")()
        try:
            while chunk := handle.read(1024 * 1024):
                decoder.decode(chunk)
            decoder.decode(b"", final=True)
        except UnicodeDecodeError:
            return EncodingInfo("cp1252", fallback=True, bom=has_bom)
    if has_bom:
        return EncodingInfo("utf-8-sig", bom=True)
    return EncodingInfo("utf-8")


def detect_delimiter(sample: str) -> str:
    """Wählt das Trennzeichen, dessen Feldanzahl am besten zur Kopfzeile passt."""
    sample = sample.replace("\r\n", "\n").replace("\r", "\n")
    best = ","
    best_score = (0.0, 0)
    for delimiter in SUPPORTED_DELIMITERS:
        rows: list[list[str]] = []
        try:
            for index, row in enumerate(
                csv.reader(io.StringIO(sample), delimiter=delimiter)
            ):
                if index >= _SNIFF_ROWS:
                    break
                if row and any(field.strip() for field in row):
                    rows.append(row)
        except csv.Error:
            continue
        if not rows:
            continue
        header_count = len(rows[0])
        if header_count <= 1:
            continue
        matching = sum(1 for row in rows if len(row) == header_count)
        score = (matching / len(rows), header_count)
        if score > best_score:
            best_score = score
            best = delimiter
    return best


def normalize_column_names(names: Sequence[str]) -> list[str]:
    """Macht leere und doppelte Spaltennamen eindeutig."""
    bases: list[str] = []
    seen_bases: set[str] = set()
    for index, raw in enumerate(names, start=1):
        name = raw.strip()
        match = _DUPLICATED.match(name)
        if match:
            base = match.group(1)
            if not base:
                name = f"Spalte {index}"
            elif base in seen_bases:
                name = f"{base} ({int(match.group(2)) + 2})"
        if not name:
            name = f"Spalte {index}"
        bases.append(name)
        seen_bases.add(name)

    used: set[str] = set()
    reserved = set(bases)
    result: list[str] = []
    for base in bases:
        if base not in used:
            result.append(base)
            used.add(base)
            continue
        suffix = 2
        while f"{base} ({suffix})" in used or f"{base} ({suffix})" in reserved:
            suffix += 1
        candidate = f"{base} ({suffix})"
        result.append(candidate)
        used.add(candidate)
    return result


def delimiter_label(delimiter: str) -> str:
    return "Tab" if delimiter == "\t" else delimiter


def encoding_label(info: EncodingInfo) -> str:
    if info.encoding == "utf-8-sig":
        return "UTF-8 mit BOM"
    if info.encoding == "utf-8":
        return "UTF-8"
    if info.encoding == "cp1252":
        return "Windows-1252"
    return info.encoding


def load_csv(
    path: str | Path,
    *,
    delimiter: str | None = None,
    encoding: str | None = None,
) -> LoadResult:
    """Lädt eine CSV-Datei vollständig als String-DataFrame."""
    try:
        return _load_csv(path, delimiter=delimiter, encoding=encoding)
    except OSError as exc:
        raise CsvLoadError(f"Die Datei konnte nicht gelesen werden: {exc}") from exc


def _load_csv(
    path: str | Path,
    *,
    delimiter: str | None = None,
    encoding: str | None = None,
) -> LoadResult:
    path = Path(path)
    if not path.exists():
        raise CsvLoadError(f"Die Datei „{path}“ wurde nicht gefunden.")
    if not path.is_file():
        raise CsvLoadError(f"„{path}“ ist keine Datei.")

    info = detect_encoding(path) if encoding is None else EncodingInfo(encoding)
    if info.encoding not in SUPPORTED_ENCODINGS:
        raise CsvLoadError(f"Nicht unterstützte Kodierung: {info.encoding}")
    if delimiter is not None and len(delimiter) != 1:
        raise CsvLoadError("Das Trennzeichen muss genau ein Zeichen sein.")

    separator = delimiter if delimiter is not None else detect_delimiter(
        _read_sample(path, info)
    )
    warnings: list[str] = []
    if info.fallback:
        warnings.append(
            "Die Datei ist nicht gültig UTF-8 und wurde als Windows-1252 gelesen."
        )

    with _utf8_source(path, info) as source:
        try:
            frame = _read_frame(source, separator)
        except pl.exceptions.NoDataError:
            raise CsvLoadError("Die Datei ist leer.") from None
        except pl.exceptions.ComputeError as exc:
            if "more fields" not in str(exc).lower():
                raise CsvLoadError(
                    f"Die Datei konnte nicht als CSV gelesen werden: {exc}"
                ) from exc
            warnings.append(
                "Mindestens eine Zeile hatte mehr Felder als die Kopfzeile; "
                "überzählige Felder wurden verworfen."
            )
            try:
                frame = _read_frame(source, separator, truncate_ragged_lines=True)
            except pl.exceptions.PolarsError as retry_exc:
                raise CsvLoadError(
                    f"Die Datei konnte nicht als CSV gelesen werden: {retry_exc}"
                ) from retry_exc
        except pl.exceptions.PolarsError as exc:
            raise CsvLoadError(
                f"Die Datei konnte nicht als CSV gelesen werden: {exc}"
            ) from exc

    names = normalize_column_names(frame.columns)
    if names != frame.columns:
        frame = frame.rename(dict(zip(frame.columns, names)))

    return LoadResult(
        frame=frame,
        delimiter=separator,
        encoding=info,
        warnings=tuple(warnings),
    )


def _read_sample(path: Path, info: EncodingInfo) -> str:
    with path.open("rb") as handle:
        raw = handle.read(_SAMPLE_BYTES)
    if info.bom and raw.startswith(codecs.BOM_UTF8):
        raw = raw[len(codecs.BOM_UTF8) :]
    encoding = "utf-8" if info.encoding == "utf-8-sig" else info.encoding
    return raw.decode(encoding, errors="replace")


def _read_frame(
    source: Path,
    separator: str,
    *,
    truncate_ragged_lines: bool = False,
) -> pl.DataFrame:
    return pl.read_csv(
        source,
        separator=separator,
        has_header=True,
        infer_schema_length=0,
        null_values=[""],
        quote_char='"',
        truncate_ragged_lines=truncate_ragged_lines,
        raise_if_empty=True,
    )


@contextmanager
def _utf8_source(path: Path, info: EncodingInfo) -> Iterator[Path]:
    """Liefert einen UTF-8-Pfad; Windows-1252 wird in eine temporäre Datei gewandelt."""
    if info.encoding in ("utf-8", "utf-8-sig"):
        yield path
        return
    if info.encoding != "cp1252":
        raise CsvLoadError(f"Nicht unterstützte Kodierung: {info.encoding}")

    fd, tmp_name = tempfile.mkstemp(prefix="csv-dis-", suffix=".csv")
    os.close(fd)
    try:
        with path.open("rb") as source, open(tmp_name, "wb") as target:
            if source.read(3) != codecs.BOM_UTF8:
                source.seek(0)
            decoder = codecs.getincrementaldecoder("cp1252")()
            while chunk := source.read(1024 * 1024):
                target.write(decoder.decode(chunk).encode("utf-8"))
            target.write(decoder.decode(b"", final=True).encode("utf-8"))
        yield Path(tmp_name)
    finally:
        try:
            Path(tmp_name).unlink(missing_ok=True)
        except OSError:
            pass
