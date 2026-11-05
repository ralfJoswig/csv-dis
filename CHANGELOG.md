# Changelog

Alle nennenswerten Änderungen an `csv-dis`. Neueste Einträge oben, je Version ein Abschnitt.

## [Unveröffentlicht] – 2026-11-05

- Verzeichnis als Git-Repository initialisiert (Branch `main`, Remote `origin` → https://github.com/ralfJoswig/csv-dis); Commit enthält den Stand von 1.1.0 und wurde gepusht.
- `.gitignore` um `csv_dis.cmd` und `start.cmd` ergänzt (lokale Startskripte, nicht Teil des Projekts).
- `AGENTS.md` und `HANDOFF.md` an die nun vorhandene Versionierung angepasst.

## [1.1.0] – 2026-10-26

Increment „v2“: Suche, Version, „Über“, Icon, Splash und Paketierung.

- v2-Umfang festgelegt (`docs/v2-spec.md`) und Suchsemantik als `docs/adr/0002-suche-markiert-statt-zu-filtern.md` begründet: Suche markiert Treffer, verändert die Ansicht nicht und durchsucht nur sichtbare Spalten.
- Versionsschema festgelegt: v1 = 1.0.0, v2 = 1.1.0; `pyproject.toml` von 0.1.0 auf 1.0.0 korrigiert.
- Lizenz festgelegt: GPLv3 wegen PyQt6 GPL-3.0-only, Copyright Ralf Joswig; Umsetzung von „Über“-Dialog und Lizenzdateien in diesem Increment.
- Suche (`search.py`): spaltenübergreifend über die sichtbaren Spalten, Begriffe UND-verknüpft pro Zeile, Teilstring case-insensitiv und literal; Treffermasken auf Polars-Serien ohne neue Abhängigkeit. 12 Unit-Tests, inklusive `ß` (kein `casefold`, damit „Straße“ nicht zu „Strasse“ wird).
- Textfilter und Suche verwenden für den Suchbegriff `str.lower()` statt `casefold()`; `ß` bleibt damit `ß` (auch im v1-Filter, mit Test).
- Suchleiste (`search_bar.py`) dauerhaft zwischen Filterleiste und Tabelle: Feld, Trefferzähler, „Zurück“/„Weiter“; `Strg+F`, `Esc`, `Enter`, `Umschalt+Enter`.
- Treffer werden im Modell gelb markiert, der aktuelle Treffer kräftiger; markierte Zellen bekommen dunkle Schrift für ausreichenden Kontrast im dunklen Theme. Navigation mit Umlauf, Scrollen zur Zeile und zur ersten passenden Spalte. 18 GUI-Tests.
- Suche läuft 200 ms nach der letzten Eingabe im Hintergrund und wird bei Filter-, Sortier- und Spaltenänderungen neu berechnet; neues Öffnen und Parser-Neuladen leeren sie. Der Zähler zeigt während der Berechnung sofort „Suche…“ statt des alten Ergebnisses.
- Version 1.1.0 aus einer Quelle (`csv_dis.__version__`); `pyproject.toml` liest sie dynamisch über `attr`, Paketmetadaten und editable Installation aktualisiert.
- „Hilfe > Über csv-dis“ (`about_dialog.py`): Version, Copyright Ralf Joswig, GPLv3-Kurzangabe, Verweis auf `LICENSE` und `THIRD-PARTY-NOTICES.md`, Laufzeitbibliotheken mit tatsächlich installierten Versionen (Python, PyQt6, Qt über `qVersion()`, Polars). 5 Tests.
- `LICENSE` mit vollständigem GPLv3-Text und `THIRD-PARTY-NOTICES.md` mit PyQt6 (GPL-3.0-only), Qt (LGPLv3), Polars (MIT) und Python (PSF) angelegt.
- Programm-Icon als `src/csv_dis/assets/csv-dis.ico` mit 16–256 px, reproduzierbar erzeugt über `tools/make_icon.py`; als Paketdatum eingebunden und über `importlib.resources` geladen. 3 Tests.
- Splash-Screen (`splash.py`, `app.py`) mit Icon, Name und Version, mindestens 800 ms sichtbar, ignoriert Klicks; bei Start mit Datei folgt der Lade-Fortschrittsdialog erst nach dem Splash. 5 Splash-Tests und 1 Startablauf-Test.
- v2-Spezifikation um Programm-Icon (`.ico`, 16–256 px) und Splash-Screen beim Start ergänzt; Abnahme in `docs/v2-spec.md` nachgezogen.
- 49 neue Tests für Suche, Version, „Über“, Icon und Splash.
- Paketierung (`tools/build_exe.py`, `tools/launcher.py`): PyInstaller baut `dist/csv-dis/csv-dis.exe` ohne Konsolenfenster mit eingebettetem Icon und Icon als Paketdatum; `LICENSE` und `THIRD-PARTY-NOTICES.md` werden daneben kopiert. PyInstaller ist Entwicklungsabhängigkeit.
- Eigene AppUserModelID `RalfJoswig.csv-dis` beim Start unter Windows, damit Fenster und Taskleiste zusammengehören.
- 7 Tests für die Paketierung: Build-Parameter, Einstiegspunkt, Lizenzkopie, App-ID sowie – wenn gebaut – GUI-Subsystem und Icon-Ressource der `.exe`.
- Insgesamt **120 Tests grün** (19 Loader, 5 GUI-Smoke, 5 GUI-Laden, 6 GUI-Parser, 7 Typen, 13 Abfrage, 10 GUI-Abfrage, 12 Suchlogik, 18 GUI-Suche, 5 „Über“, 3 Icon, 5 Splash, 1 Startablauf, 4 Version, 7 Paketierung).
- Messung Suche auf 1 Mio. × 5 Spalten (50,1 MB): 46–129 ms Rechenzeit, Ende-zu-Ende 310–328 ms inklusive 200 ms Verzögerung; Ereignisschleife blieb während der Suche aktiv.
- Beide Beispieldateien erneut geladen und durchsucht; Fenster, Titelleiste, Treffer, „Über“-Dialog und Splash per Screenshot visuell geprüft.
- Gepackte `.exe` geprüft: Splash (420 × 230) nach 1,2 s, Datei geöffnet (46 × 29 und 209 × 3), Suche über UI Automation (`PC0-0-0-0` → „1 von 1 Treffern“), Taskleiste zeigt das csv-dis-Icon. Bei `python -m csv_dis` zeigt die Taskleiste weiterhin das Python-Host-Icon; dokumentierte Einschränkung.
- Abnahme v2 aus `docs/v2-spec.md` vollständig durchgeführt (elf Punkte) und in `STATUS.md` protokolliert.

## [1.0.0] – 2026-10-26

Increment „v1“: Parser, Typen, Filter, Sortierung, Spaltenauswahl, Hintergrundladen.

- Spaltentypen ergänzt (`column_types.py`): Zahl, Datum (`YYYY-MM-DD`, `YYYY-MM-DD HH:MM[:SS]`) und Text aus allen nicht leeren Werten; führende Nullen und Einheiten gelten als Text.
- Filter-Engine (`query.py`): typgerechte Operatoren, UND-Verknüpfung, Originaltext bleibt unverändert.
- Sortierung nach genau einer Spalte mit typgerechter Reihenfolge; leere Zellen stehen in beiden Richtungen am Ende.
- Trichter-Symbol im Spaltenkopf (`header.py`) öffnet den Filterdialog; zusätzlich Doppelklick und Kopfmenü.
- Filterleiste mit entfernbaren Einträgen und „Alle entfernen“; ungültige Eingaben werden im Dialog markiert.
- Sortierung per Kopfklick (auf-/absteigend) mit Sortierpfeil; Spalten über das Kopfmenü aus- und einblendbar.
- Statuszeile „X von Y Zeilen“; Hinweis, wenn alle Spalten ausgeblendet sind.
- Live-Anwendung nach 200 ms im Hintergrund-Thread; neue Eingaben brechen die laufende Berechnung ab.
- Öffnen im Hintergrund mit unbestimmter Fortschrittsanzeige und „Abbrechen“; das Fenster bleibt bedienbar, eine neue Datei ersetzt den laufenden Ladevorgang.
- Parser-Korrektur: Dialog „Trennzeichen und Encoding…“ lädt die Datei mit manueller Auswahl neu; Filter, Sortierung und ausgeblendete Spalten werden zurückgesetzt, Fehler lassen die bisherige Ansicht stehen.
- 40 neue Tests: Typen, Filter/Sortierung, GUI-Abläufe, Hintergrundladen und Parser-Korrektur; insgesamt 64 Tests grün.
- Messungen: 1 Mio. × 5 Spalten (50,1 MB) Typen 0,20 s, Filter+Sortierung 0,02 s; 300.000 × 30 Spalten (118,1 MB) Typen 0,34 s, Filter+Sortierung 0,01 s. `open_path` kehrt bei 1 Mio. Zeilen nach 0,001 s zurück, die Datei ist nach 0,32 s sichtbar.
- Beide Beispieldateien erneut geladen, typisiert, gefiltert und sortiert.
- Abnahme v1 aus `docs/v1-spec.md` am 2026-10-26 manuell mit positivem Ergebnis durchgeführt: beide Beispieldateien gesichtet, 1 Mio. Zeilen geöffnet/gefiltert/sortiert, echte Drag-&-Drop-Geste inklusive Ablehnung von URL und Ordner, Filter und Spalten bedient, Neustart ohne Zustand.

## [0.1.0] – 2026-10-25

Projektstart: Grundgerüst, Loader, Dokumentation.

- Ziel und v1-Umfang abgestimmt: read-only Anzeige einer CSV-Datei mit Filtern, Sortierung und ausblendbaren Spalten.
- Nicht-Ziele festgelegt: Bearbeiten, Export, Server/Datenbank, Mehrfachdateien, Gruppieren/Rechnen/Diagramme.
- Technik festgelegt: Python ≥ 3.12, PyQt6, Polars 2.x; ADR 0001 angelegt.
- `CONTEXT.md` (Begriffe) und `docs/v1-spec.md` (Verhalten und Abnahme) angelegt.
- `AGENTS.md`, `STATUS.md` und `TODO.md` an den abgestimmten Stand angepasst.
- Grundgerüst und CSV-Loader implementiert: PyQt6-Fenster, Polars-Loader, BOM-/Encoding-/Trennzeichen-Erkennung, Kopfzeilen-Normalisierung, Umgang mit unregelmäßigen Zeilen.
- Tests mit pytest eingerichtet: 24 Tests, GUI-Smoke-Test offscreen.
- Drag & Drop zum Öffnen lokaler Dateien ergänzt; URLs und Ordner werden abgelehnt, bei mehreren Dateien wird nur die erste geöffnet.
- 1-Mio.-Zeilen-Smoke-Test: 66 MB, 5 Spalten in 0,18 s geladen.
- 100-MB-Smoke-Test: 118 MB, 30 Spalten (300.000 Zeilen) in 1,12 s geladen.
- `tools/make_large_csv.py` für reproduzierbare große Testdateien ergänzt.
- Dokumentationsprüfung: Testbefehl in der Spezifikation auf die lokale `.venv` umgestellt; Paketbeschreibung auf den aktuellen Funktionsumfang gekürzt.
- `HANDOFF.md` als ausführliche Übergabe angelegt; `STATUS.md` und `AGENTS.md` verweisen darauf.
