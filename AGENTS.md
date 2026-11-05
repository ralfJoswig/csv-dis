# AGENTS.md

## Projekt

- `csv-dis` ist ein lokales Windows-Programm, das **eine** CSV-Datei als Tabelle anzeigt, Zeilen filtert, sortiert, Spalten ausblendet und spaltenübergreifend sucht. Die Datei wird nie verändert. Öffnen per Dialog oder Drag & Drop; nur lokale Dateien, eine Datei pro Fenster.
- Nicht-Ziele: Bearbeiten, Export, Server/Datenbank, mehrere Dateien gleichzeitig, Gruppieren/Rechnen/Diagramme.
- Stack: Python ≥ 3.12 (lokal 3.13), PyQt6, Polars 2.x, Tests mit pytest. Eigenständiger Code; nichts aus `md-dis` übernehmen.
- Der Loader liest alle Spalten als String (`infer_schema_length=0`), damit der Originaltext erhalten bleibt. Spaltentypen sind nur für Sortierung und Filter gedacht, nicht für die Anzeige.
- Zielbild und Abnahme: `docs/v2-spec.md` (aktueller, abgenommener Increment); v1-Grundlage: `docs/v1-spec.md`. Begriffe: `CONTEXT.md`. Datenmodell: `docs/adr/0001-polars-datenmodell.md`; Suchsemantik: `docs/adr/0002-suche-markiert-statt-zu-filtern.md`.
- Auslieferung als gepackte Anwendung `dist\csv-dis\csv-dis.exe` (PyInstaller, `tools/build_exe.py`); nur so zeigt die Windows-Taskleiste das eigene Icon. Lizenz: GPLv3, Texte in `LICENSE` und `THIRD-PARTY-NOTICES.md`.
- Das Verzeichnis ist seit 2026-11-05 ein Git-Repository (Branch `main`, Remote `origin` → https://github.com/ralfJoswig/csv-dis). `csv_dis.cmd` und `start.cmd` sind lokal ignoriert.

## Befehle

Alle Befehle aus dem Projektverzeichnis mit der lokalen `.venv`:

- Abhängigkeiten: `.\.venv\Scripts\python.exe -m pip install -e ".[dev]"`
- Start: `.\.venv\Scripts\python.exe -m csv_dis`
- Start mit Datei: `.\.venv\Scripts\python.exe -m csv_dis "C:\pfad\datei.csv"`
- Alle Tests: `.\.venv\Scripts\python.exe -m pytest`
- Ein Test: `.\.venv\Scripts\python.exe -m pytest tests\test_csv_loader.py::test_load_bom_semicolon`
- Große Testdatei: `.\.venv\Scripts\python.exe tools\make_large_csv.py`
- Paket bauen: `.\.venv\Scripts\python.exe tools\build_exe.py` → `dist\csv-dis\csv-dis.exe`
- Icon neu erzeugen: `.\.venv\Scripts\python.exe tools\make_icon.py`

GUI-Tests laufen ohne Fenster über `QT_QPA_PLATFORM=offscreen` (gesetzt in `tests/conftest.py`).

## Pflicht am Ende jeder Arbeitssitzung

`STATUS.md`, `CHANGELOG.md` und `TODO.md` sind das Gedächtnis des Projekts. Vor dem Beenden immer alle drei aktualisieren. `HANDOFF.md` ist die ausführliche Übergabe an die nächste Sitzung und wird bei jedem abgeschlossenen Increment mitgezogen.

- `STATUS.md`: was läuft, was nicht, wie man es startet, nächster konkreter Schritt.
- `CHANGELOG.md`: neueste Einträge oben, mit Datum und kurzer Liste der Änderungen.
- `TODO.md`: offene Aufgaben pflegen; erledigte Punkte abhaken oder entfernen.

Regeln:

- Nur verifizierte Aussagen eintragen. Nichts als funktionierend beschreiben, was nicht gestartet oder getestet wurde.
- Die drei Dateien müssen zueinander, zur Spezifikation und zum Code passen. Widersprüche sind ein Fehler.
- Nach einem abgeschlossenen Increment den Status auf den nächsten Schritt umstellen, nicht mehrere Stände sammeln.

## Verifikation

- Vor dem Abschluss `.\.venv\Scripts\python.exe -m pytest` ausführen.
- Abnahme: siehe `docs/v2-spec.md` (v1: `docs/v1-spec.md`); ein Increment gilt erst als fertig, wenn der beschriebene Test tatsächlich gelaufen ist.
- Bei Änderungen an Icon, Startablauf oder Abhängigkeiten zusätzlich `tools\build_exe.py` laufen lassen und die `.exe` starten; `pytest` baut nicht selbst.
- Beim Laden immer beide echten Beispieldateien prüfen (Pfade in `docs/v1-spec.md`); sie decken BOM, Semikolon, Komma und Anführungszeichen ab.
