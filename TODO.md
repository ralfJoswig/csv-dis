# TODO

## Versionierung

- [x] Lokales Git-Repository auf Branch `main` anlegen und ersten Commit erstellen.
- [x] `.gitignore` um `csv_dis.cmd` und `start.cmd` ergänzen.

## v1 – Parser

- [x] Trennzeichen und Encoding nach dem Öffnen manuell korrigierbar machen.
- [x] Öffnen in den Hintergrund verlagern und eine Fortschrittsanzeige ergänzen.

## v1 – Daten und Typen

- [x] Spaltentyp (Zahl/Datum/Text) automatisch erkennen; Originaltext unverändert anzeigen.
- [x] Leere Zellen beim Sortieren ans Ende stellen.
- [x] Filter-Engine (UND) und Sortierung in Polars.
- [x] Hintergrund-Thread mit Abbruch für Filter und Sortierung.

## v1 – Oberfläche

- [x] Tabelle mit virtualisiertem Modell für 1 Mio. Zeilen.
- [x] Datei per Dialog und Drag & Drop öffnen; URLs und Ordner ablehnen; bei mehreren Dateien nur die erste öffnen.
- [x] Filter-Popup pro Spalte und Filterleiste mit entfernbaren Filtern.
- [x] Sortierung per Klick auf die Kopfzeile (eine Spalte, auf/ab).
- [x] Spalten per Kopfmenü ein-/ausblenden; Statuszeile „X von Y Zeilen“.
- [x] Live-Anwendung mit etwa 200 ms Verzögerung; Fenster bleibt bedienbar.
- [x] Fehlerdialog bei nicht lesbarer Datei; Warnungen bei Parserproblemen.
- [x] Oberfläche auf Deutsch.

## v1 – Abnahme

- [x] Generator für eine 1-Mio.-Zeilen-Testdatei (`tools/make_large_csv.py`).
- [x] Beide echten Beispieldateien laden und automatisiert prüfen (46 × 29, 209 × 3).
- [x] Sichtprüfung aller Werte der Beispieldateien von Hand.
- [x] 1-Mio.-Zeilen-Datei im GUI öffnen, während der Ladevorgang eine Fortschrittsanzeige zeigt.
- [x] Abnahmetest aus `docs/v1-spec.md` vollständig durchführen und in `STATUS.md` protokollieren (Sichtprüfung, echte Drag-&-Drop-Geste, Neustart).

## v2 – Suche, Version, „Über“, Icon, Splash, Paketierung

Details: `docs/v2-spec.md`, Begründung: `docs/adr/0002-suche-markiert-statt-zu-filtern.md`.

- [x] Dauerhafte Suchleiste mit Feld, Trefferzähler, „Zurück“/„Weiter“; `Strg+F` und `Esc`.
- [x] Trefferberechnung: Zeile, alle Begriffe, sichtbare Spalten, case-insensitiv, literal; im Hintergrund mit Abbruch.
- [x] Markierung aller Trefferzellen, aktueller Treffer hervorgehoben; Scrollen zu Zeile und passender Spalte.
- [x] Suche bei Filter-, Sortier- und Spaltenänderungen neu berechnen; beim Öffnen und Parser-Neuladen leeren.
- [x] Tests für Trefferlogik und GUI; Messung mit 1 Mio. Zeilen dokumentieren.
- [x] Version genau einmal in `csv_dis.__version__`; `pyproject.toml` dynamisch; 1.1.0.
- [x] `LICENSE` mit GPLv3-Volltext und `THIRD-PARTY-NOTICES.md` anlegen.
- [x] „Hilfe > Über csv-dis“ mit Version, Copyright Ralf Joswig, GPLv3-Kurzangabe und Laufzeitbibliotheken.
- [x] Programm-Icon als `.ico` (16–256 px) im Paket; Motiv im Projekt erzeugen (`tools/make_icon.py`, Tabellenraster mit Trichter); für Titelleiste, Taskleiste und „Über“-Dialog gesetzt.
- [x] Splash-Screen beim Start mit Icon, Name und Version; Mindestdauer 800 ms, danach selbstständig ausblenden, Klicks werden ignoriert.
- [x] Abnahme aus `docs/v2-spec.md` durchführen und in `STATUS.md` protokollieren.
- [x] Taskleisten-Icon am laufenden Programm sichtprüfen; dafür PyInstaller-Build `dist/csv-dis/csv-dis.exe` ergänzt (`tools/build_exe.py`, eigenes Icon und AppUserModelID).
- [x] PyInstaller als Entwicklungsabhängigkeit, Build-Doku und Paketierungstests ergänzen; `LICENSE` und `THIRD-PARTY-NOTICES.md` mit in den Build-Ordner kopieren.
- [x] v2 formal abschließen.

## Erledigt

- [x] Projekt-Dokumentation und Arbeitsablauf definiert.
- [x] Ziel, Umfang und Abnahme für v1 abgestimmt.
- [x] Grundgerüst und CSV-Loader implementiert.
- [x] Typerkennung, Filter, Sortierung, Spaltenauswahl, Hintergrundladen, Parser-Korrektur und Live-Aktualisierung implementiert; 64 Tests grün.
- [x] Abnahme v1 am 2026-10-26 manuell mit positivem Ergebnis durchgeführt (alle fünf Punkte).
- [x] v2 umgesetzt: Suche, Version 1.1.0, „Über“-Dialog, Lizenzdateien, Icon, Splash und PyInstaller-Build; 120 Tests grün; Abnahme vollständig.
- [x] `HANDOFF.md` als ausführliche Übergabe angelegt.
