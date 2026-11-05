from __future__ import annotations

import codecs
from pathlib import Path

import pytest

from csv_dis.csv_loader import (
    CsvLoadError,
    detect_delimiter,
    detect_encoding,
    load_csv,
    normalize_column_names,
)


def write_bytes(tmp_path: Path, name: str, data: bytes) -> Path:
    path = tmp_path / name
    path.write_bytes(data)
    return path


def write_text(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8", newline="")
    return path


def test_detect_delimiter() -> None:
    assert detect_delimiter("a;b;c\n1;2;3\n") == ";"
    assert detect_delimiter("a,b,c\n1,2,3\n") == ","
    assert detect_delimiter("a\tb\tc\n1\t2\t3\n") == "\t"
    assert detect_delimiter("a|b|c\n1|2|3\n") == "|"
    assert detect_delimiter('"a,b";c\n"x,y";z\n') == ";"


def test_detect_encoding_utf8_bom(tmp_path: Path) -> None:
    path = write_bytes(
        tmp_path, "bom.csv", codecs.BOM_UTF8 + "a;b\n1;2\n".encode()
    )
    info = detect_encoding(path)
    assert info.encoding == "utf-8-sig"
    assert info.bom is True
    assert info.fallback is False


def test_detect_encoding_utf8(tmp_path: Path) -> None:
    path = write_text(tmp_path, "utf8.csv", "a;b\nMüller;2\n")
    info = detect_encoding(path)
    assert info.encoding == "utf-8"
    assert info.fallback is False


def test_detect_encoding_cp1252(tmp_path: Path) -> None:
    path = write_bytes(
        tmp_path, "cp1252.csv", "a;b\nMüller;2\n".encode("cp1252")
    )
    info = detect_encoding(path)
    assert info.encoding == "cp1252"
    assert info.fallback is True


def test_load_bom_semicolon(tmp_path: Path) -> None:
    path = write_bytes(
        tmp_path,
        "bom.csv",
        codecs.BOM_UTF8 + "Name;Wert\nÄ;1\nB;2\n".encode(),
    )
    result = load_csv(path)
    assert result.frame.columns == ["Name", "Wert"]
    assert result.frame.to_dicts() == [
        {"Name": "Ä", "Wert": "1"},
        {"Name": "B", "Wert": "2"},
    ]
    assert result.delimiter == ";"
    assert result.encoding.encoding == "utf-8-sig"
    assert result.warnings == ()


def test_load_comma_quotes(tmp_path: Path) -> None:
    path = write_text(tmp_path, "quotes.csv", '"a","b"\n"x,1","y"\n')
    result = load_csv(path)
    assert result.frame.columns == ["a", "b"]
    assert result.frame.to_dicts() == [{"a": "x,1", "b": "y"}]
    assert result.delimiter == ","


def test_load_multiline_quoted_field(tmp_path: Path) -> None:
    path = write_text(tmp_path, "multi.csv", 'a;b\n"Zeile 1\nZeile 2";x\n')
    result = load_csv(path)
    assert result.delimiter == ";"
    assert result.frame.to_dicts() == [{"a": "Zeile 1\nZeile 2", "b": "x"}]


def test_load_crlf(tmp_path: Path) -> None:
    path = write_bytes(tmp_path, "crlf.csv", b"a;b\r\n1;2\r\n")
    result = load_csv(path)
    assert result.frame.to_dicts() == [{"a": "1", "b": "2"}]



def test_load_tab(tmp_path: Path) -> None:
    path = write_text(tmp_path, "tab.csv", "a\tb\n1\t2\n")
    result = load_csv(path)
    assert result.delimiter == "\t"
    assert result.frame.to_dicts() == [{"a": "1", "b": "2"}]


def test_load_cp1252_fallback(tmp_path: Path) -> None:
    path = write_bytes(
        tmp_path, "cp1252.csv", "Name;Ort\nMüller;Köln\n".encode("cp1252")
    )
    result = load_csv(path)
    assert result.frame.to_dicts() == [{"Name": "Müller", "Ort": "Köln"}]
    assert result.encoding.encoding == "cp1252"
    assert any("Windows-1252" in warning for warning in result.warnings)


def test_load_short_and_long_rows(tmp_path: Path) -> None:
    path = write_text(tmp_path, "ragged.csv", "a;b;c\n1;2\n3;4;5;6\n")
    result = load_csv(path)
    assert result.frame.to_dicts() == [
        {"a": "1", "b": "2", "c": None},
        {"a": "3", "b": "4", "c": "5"},
    ]
    assert any("mehr Felder" in warning for warning in result.warnings)


def test_load_normalizes_headers(tmp_path: Path) -> None:
    path = write_text(tmp_path, "headers.csv", "a;a;;c\n1;2;3;4\n")
    result = load_csv(path)
    assert result.frame.columns == ["a", "a (2)", "Spalte 3", "c"]


def test_load_preserves_na_and_empty(tmp_path: Path) -> None:
    path = write_text(tmp_path, "nulls.csv", "a;b\nNA;x\n;y\n")
    result = load_csv(path)
    assert result.frame.to_dicts() == [
        {"a": "NA", "b": "x"},
        {"a": None, "b": "y"},
    ]


def test_manual_delimiter_override(tmp_path: Path) -> None:
    path = write_text(tmp_path, "semicolon.csv", "a;b\n1;2\n")
    result = load_csv(path, delimiter=",")
    assert result.delimiter == ","
    assert result.frame.columns == ["a;b"]
    assert result.frame.to_dicts() == [{"a;b": "1;2"}]


def test_manual_encoding_override(tmp_path: Path) -> None:
    path = write_bytes(tmp_path, "cp1252.csv", "Name\nMüller\n".encode("cp1252"))
    result = load_csv(path, encoding="cp1252")
    assert result.frame.to_dicts() == [{"Name": "Müller"}]
    assert result.encoding.fallback is False


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(CsvLoadError):
        load_csv(tmp_path / "missing.csv")


def test_directory_rejected(tmp_path: Path) -> None:
    with pytest.raises(CsvLoadError):
        load_csv(tmp_path)


def test_empty_file(tmp_path: Path) -> None:
    path = write_text(tmp_path, "empty.csv", "")
    with pytest.raises(CsvLoadError):
        load_csv(path)


def test_normalize_column_names() -> None:
    assert normalize_column_names(["a", "a_duplicated_0", "", "c"]) == [
        "a",
        "a (2)",
        "Spalte 3",
        "c",
    ]
