# Handoff

Übergabe an die nächste Arbeitssitzung. Stand: 2026-10-26.
Kurzfassung: `STATUS.md` · offene Punkte: `TODO.md` · Historie: `CHANGELOG.md` · Regeln: `AGENTS.md`.

## Ziel

Lokaler Windows-CSV-Betrachter: **eine** Datei, read-only, Tabelle mit Filtern (pro Spalte, UND-verknüpft), Sortierung (eine Spalte), ausblendbaren Spalten und spaltenübergreifender Suche. Bis etwa 1 Mio. Zeilen / 100 MB. Oberfläche und Dokumentation auf Deutsch. Das Verzeichnis ist seit 2026-11-05 ein Git-Repository (Branch `main`, Remote `origin` → https://github.com/ralfJoswig/csv-dis). Weitergabe erfolgt als gepackte Anwendung `dist/csv-dis/`.

## Fertig und verifiziert

- **Umgebung:** Python 3.13.14, lokale `.venv`, PyQt6 6.11.0, Qt 6.11.2 (Laufzeit, `qVersion()`), Polars 2.1.0, pytest 9.1.1, PyInstaller 6.22.3 (nur Build). `pyproject.toml` pinnt `PyQt6>=6.7,<7` und `polars>=2.1,<3`; `pyinstaller>=6` steht in `dev`.
- **Loader** (`src/csv_dis/csv_loader.py`): BOM, UTF-8 strikt mit Windows-1252-Fallback und Warnung, Trennzeichen `;` `,` Tab `|` (Feldanzahl der Kopfzeile als Anker), RFC 4180 inklusive mehrzeiliger Felder, Kopfzeilen-Normalisierung, kurze Zeilen auffüllen, überzählige Felder melden, `OSError` wird zu `CsvLoadError`. `delimiter` und `encoding` lassen sich als Keyword-Parameter erzwingen; die Oberfläche nutzt das über den Parser-Dialog.
- **Typerkennung** (`src/csv_dis/column_types.py`): pro Spalte alle nicht leeren Werte; Zahl = Vorzeichen + Ziffern + höchstens ein Dezimalpunkt, führende Nullen und Einheiten ⇒ Text; Datum nur `YYYY-MM-DD` oder `YYYY-MM-DD HH:MM[:SS]` mit gültigem Kalender; sonst Text. Vektorisiert über Polars, leere Zellen (`null` oder `""`) zählen nicht.
- **Abfrage** (`src/csv_dis/query.py`): Filter werden zu Polars-Ausdrücken, mehrere Filter UND-verknüpft, `df.filter(...)`; Sortierung nach genau einer Spalte, typgerecht, leere Zellen in beiden Richtungen am Ende. Der geladene DataFrame bleibt unverändert. Ungültige Werte werfen `QueryError` mit deutscher Meldung.
- **GUI** (`main_window.py`, `model.py`, `header.py`, `filter_dialog.py`, `parser_dialog.py`, `app.py`):
  - Datei-Dialog, Drag & Drop (nur lokale Dateien; URLs und Ordner abgelehnt; bei mehreren die erste plus fünf Sekunden Hinweis).
  - Öffnen inklusive Typerkennung läuft im Hintergrund mit unbestimmter Fortschrittsanzeige und „Abbrechen“; das Fenster bleibt bedienbar. Eine neue Datei ersetzt den laufenden Ladevorgang, veraltete Ergebnisse werden über eine Generationsnummer verworfen.
  - „Datei > Trennzeichen und Encoding…“ öffnet `ParserDialog` mit den aktuellen Werten und lädt die Datei mit manueller Auswahl neu. Filter, Sortierung, ausgeblendete Spalten und Suche werden zurückgesetzt; bei einem Ladefehler bleibt die bisherige Ansicht stehen.
  - Trichter-Symbol im Spaltenkopf öffnet den Filterdialog; Doppelklick und Kopfmenü gehen ebenfalls.
  - Filterleiste mit entfernbarem Eintrag pro Filter und „Alle entfernen“.
  - Kopfklick sortiert aufsteigend, erneuter Klick absteigend; Sortierpfeil wird gesetzt.
  - Kopfmenü: sortieren, filtern, Filter der Spalte entfernen, Spalte aus-/einblenden, Untermenü „Spalten“ mit allen Häkchen.
  - Statuszeile „X von Y Zeilen“, Trennzeichen, Encoding; Hinweis, wenn alle Spalten ausgeblendet sind.
  - Filter und Sortierung laufen 200 ms nach der letzten Eingabe in einem Hintergrund-Task; neue Eingaben setzen ein Abbruch-Flag, veraltete Ergebnisse werden über eine Generationsnummer verworfen.
- **Suche** (`search.py`, `search_bar.py`, `model.py`, `main_window.py`):
  - Dauerhafte Leiste zwischen Filterleiste und Tabelle: Feld mit Platzhalter „Sichtbare Spalten durchsuchen…“, Zähler, „Zurück“/„Weiter“. `Strg+F` fokussiert das Feld, `Esc` leert die Suche, `Enter`/`Umschalt+Enter` navigieren.
  - Begriffe werden an Leerzeichen getrennt; eine Zeile ist Treffer, wenn jeder Begriff mindestens einmal in einer sichtbaren Zelle vorkommt. Teilstring, case-insensitiv, literal; Umlaute werden nicht vereinfacht; `ß` bleibt `ß`.
  - `search_frame()` liefert `SearchHits`: Trefferzeilen als Polars-Serie, Zellmasken pro Spalte, Begriffe. Ohne numpy, direkt auf Polars-Serien (`arg_true()`, `item()`).
  - Das Modell markiert alle passenden Zellen der Trefferzeilen gelb, den aktuellen Treffer kräftiger. Navigation läuft mit Umlauf und scrollt zur Zeile sowie zur ersten passenden Spalte.
  - Die Suche läuft 200 ms nach der letzten Eingabe in `_SearchTask` im Thread-Pool; neue Eingaben brechen sie über ein `threading.Event` ab, veraltete Ergebnisse werden über `_search_generation` verworfen. Der Zähler zeigt sofort „Suche…“ und leert die alten Markierungen.
  - Bei Filter-, Sortier- und Spaltenänderungen bleibt der Suchtext erhalten und wird auf der neuen Ansicht neu berechnet (`_restart_search`). Neues Öffnen und Parser-Neuladen leeren sie (`_reset_search`).
- **Version:** genau eine Quelle, `csv_dis.__version__ = "1.1.0"`; `pyproject.toml` nutzt `dynamic = ["version"]` und `attr = "csv_dis.__version__"`. Die installierte Metadatenversion ist 1.1.0.
- **„Über“-Dialog** (`about_dialog.py`): modal, Icon, `csv-dis 1.1.0`, Copyright Ralf Joswig, GPLv3-Kurzangabe mit Verweis auf `LICENSE`, Tabelle der Laufzeitbibliotheken mit installierten Versionen (Python, PyQt6, Qt über `qVersion()`, Polars) und Verweis auf `THIRD-PARTY-NOTICES.md`. Schließt mit „OK“.
- **Lizenz:** App GPLv3 wegen PyQt6 GPL-3.0-only. `LICENSE` enthält den vollständigen GPLv3-Text; `THIRD-PARTY-NOTICES.md` enthält PyQt6 (GPL-3.0-only), Qt (LGPLv3), Polars (MIT) und Python (PSF-Lizenz).
- **Icon:** `src/csv_dis/assets/csv-dis.ico` mit 16, 24, 32, 48, 64, 128, 256 px, erzeugt von `tools/make_icon.py` (Tabellenraster mit Trichter, ohne externe Design-Datei). Über `importlib.resources` geladen (`resources.py`), an `QApplication` und `MainWindow` gesetzt, im „Über“-Dialog sichtbar. Paketdaten sind in `pyproject.toml` eingetragen.
- **Splash:** `splash.py` zeichnet Icon, Name, Version und Untertitel auf 420 × 230 px. `SplashScreen` ignoriert Mausklicks und verschwindet nur über `finish()`. `app.main` zeigt ihn mindestens 800 ms (`SPLASH_MIN_MS`), öffnet eine Datei aus der Kommandozeile erst danach und erzeugt beim Öffnen weiterer Dateien keinen Splash.
- **Paketierung** (`tools/build_exe.py`, `tools/launcher.py`): PyInstaller baut `dist/csv-dis/csv-dis.exe` (`--windowed`) mit eingebettetem Icon und dem Icon als Paketdatum. `LICENSE` und `THIRD-PARTY-NOTICES.md` werden anschließend neben die `.exe` kopiert. Build-Ordner: 158 Dateien, 251,5 MB; `.exe` allein 4,1 MB. PyInstaller 6.22.3 ist Entwicklungsabhängigkeit, keine Laufzeitabhängigkeit.
- **Taskleiste:** Das Fenster liefert gültige `WM_GETICON`-Handles, die Titelleiste zeigt immer das csv-dis-Icon. Die Taskleiste zeigt es zuverlässig nur bei der gepackten `.exe`; beim Start über `python -m csv_dis` bleibt es beim Python-Host-Icon. Die App setzt deshalb zusätzlich die AppUserModelID `RalfJoswig.csv-dis`.
- **Tests:** **120 grün**: 19 Loader, 5 GUI-Smoke, 5 GUI-Laden, 6 GUI-Parser, 7 Typen, 13 Abfrage, 10 GUI-Abfrage, 12 Suchlogik, 18 GUI-Suche, 5 „Über“, 3 Icon, 5 Splash, 1 Startablauf, 4 Version, 7 Paketierung. GUI offscreen.
- **Messungen:** 1 Mio. × 5 Spalten (50,1 MB): laden 0,11 s, Typen 0,20 s, Filter+Sortierung 0,02 s; 300.000 × 30 Spalten (118,1 MB): 0,18 / 0,34 / 0,01 s. Suche auf 1 Mio. Zeilen: 46–129 ms Rechenzeit je Begriff, Ende-zu-Ende 310–328 ms inklusive 200 ms Verzögerung; die Ereignisschleife lief während der Suche weiter. Im GUI-Pfad mit 1 Mio. Zeilen kehrt `open_path` nach 0,001 s zurück, die Datei ist nach 0,32 s sichtbar.
- **Beispieldateien:** beide geladen (46 × 29 und 209 × 3), Typen geprüft, gefiltert, sortiert und durchsucht. Zwei Begriffe aus verschiedenen Spalten derselben Zeile ergeben je Datei genau einen Treffer; ein unbekannter Begriff ergibt „0 Treffer“.
- **Visuell geprüft:** Fenster mit Titelleiste und Suchleiste, gelbe Treffer, „Über“-Dialog und Splash per Screenshot; Icon-Größen und `ICON_BIG`/`ICON_SMALL`-Handles des Fensters geprüft.
- **Gepackte Anwendung:** `dist/csv-dis/csv-dis.exe` gestartet: Splash nach 1,2 s (420 × 230, Icon, Name, Version 1.1.0), Fenster mit `_produktliste.csv` (209 × 3) und `Geräteübersicht 20261025.csv` (46 × 29), Suche `PC0-0-0-0` → „1 von 1 Treffern“ mit markierter Zelle (Text per UI Automation gesetzt, Screenshots geprüft), Taskleiste mit csv-dis-Icon, Lizenzdateien im Build-Ordner.

## Abnahme

v1 ist am 2026-10-26 vollständig manuell mit positivem Ergebnis abgenommen (alle fünf Punkte aus `docs/v1-spec.md`): beide Beispieldateien gesichtet, 1 Mio. Zeilen geöffnet/gefiltert/sortiert, echte Drag-&-Drop-Geste inklusive Ablehnung von URL und Ordner, Filter und Spalten bedient, Parser korrigiert, Neustart ohne Zustand.

v2 ist vollständig abgenommen: die elf Punkte aus `docs/v2-spec.md` sind geprüft und in `STATUS.md` protokolliert. Punkt 11 (gepackte Anwendung) wurde am 2026-10-26 an `dist/csv-dis/csv-dis.exe` mit Screenshots von Splash, Fenster, Suche und Taskleiste durchgeführt.

## Nächster Schritt

1. v2 ist abgeschlossen; es gibt keinen offenen Punkt.
2. Für einen nächsten Increment zuerst `docs/v3-spec.md` anlegen (Ziel, Nicht-Ziele, Abnahme), dann umsetzen.
3. Bei späteren Änderungen an der Suche `docs/v2-spec.md`, ADR 0002, `CONTEXT.md` und die Suchtests gemeinsam pflegen.
4. Bei Änderungen an Icon oder Startablauf `tools/build_exe.py` erneut laufen lassen und die `.exe` prüfen; die Tests allein erkennen einen veralteten Build nicht.

## Befehle

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pytest tests\test_search.py
.\.venv\Scripts\python.exe -m pytest tests\test_gui_search.py
.\.venv\Scripts\python.exe -m pytest tests\test_about.py tests\test_icon.py tests\test_splash.py tests\test_startup.py tests\test_version.py tests\test_packaging.py
.\.venv\Scripts\python.exe -m csv_dis "C:\pfad\datei.csv"
.\dist\csv-dis\csv-dis.exe "C:\pfad\datei.csv"
.\.venv\Scripts\python.exe tools\build_exe.py
.\.venv\Scripts\python.exe tools\make_large_csv.py --rows 1000000
.\.venv\Scripts\python.exe tools\make_icon.py --preview "%TEMP%\csv-dis-icon.png"
```

## Fallstricke

- **Leere Zellen:** der Loader nutzt `null_values=[""]`, echte Daten haben also `null`. Tests und Engine behandeln zusätzlich `""`, damit direkt gebaute DataFrames funktionieren.
- **Groß-/Kleinschreibung:** Textfilter und Suche nutzen `str.to_lowercase()` und `str.contains(..., literal=True)`. `"APF"` trifft „Apfel“, aber nicht „Äpfel“ – das ist korrekt, weil ä ≠ a. Für Filter- und Suchbegriffe `str.lower()` verwenden, **nicht** `casefold()`: `casefold("ß")` ergibt `"ss"` und würde „Straße“ nicht mehr treffen.
- **Sortierung:** Hilfsspalten `__leer` und `__schluessel` werden vor der Rückgabe entfernt; `maintain_order=True` hält gleiche Schlüssel stabil. Zahlen werden mit `strict=False` gecastet, damit `""` nicht wirft.
- **Datum:** `_date_expr` kombiniert drei `strptime`-Varianten mit `coalesce` (volles Datum/Uhrzeit, angehängte `:00`, reines Datum).
- **Header:** `FilterHeader` ersetzt die Standard-Kopfzeile; das Trichter-Symbol liegt 26 px vor dem rechten Rand, damit es den Sortierpfeil nicht überdeckt. Klicks auf das Symbol lösen kein Sortieren aus.
- **Live-Pfad:** Mutationen planen nur ein (200 ms, `_schedule_query`); `apply_now()` rechnet synchron und ist der deterministische Weg in Tests. GUI-Tests für den Live-Pfad warten mit `QTest.qWait(600)`.
- **Öffnen:** `open_path()` lädt im Hintergrund (`_LoadTask`) und zeigt einen nicht-modalen `QProgressDialog` mit unbestimmtem Fortschritt. `_close_progress()` setzt zuerst `_progress = None` und blockiert Signale, sonst löst `close()` über `canceled` eine Rekursion aus. `cancel()` allein emittiert kein `canceled`; der Abbrechen-Knopf schon.
- **Generationen:** Laden, Abfragen und Suche haben getrennte Zähler. `load_path()` (synchron, für Tests) erhöht ebenfalls die Ladegeneration und bricht einen laufenden Ladevorgang ab, sonst könnte dessen Ergebnis die synchron geladene Datei überschreiben.
- **Parser-Korrektur:** `_LoadTask` und `load_csv` nehmen `delimiter`/`encoding` als Keyword-Argumente. Tests, die `main_window.load_csv` verlangsamen, müssen `**kwargs` durchreichen, sonst blockiert der Fehlerdialog den Testlauf. Ein cp1252-Fallback löst beim Laden eine Warnung (`QMessageBox.warning`) aus; in Tests entweder `encoding="cp1252"` explizit setzen oder den Dialog patchen.
- **Suche ≠ Filter:** Die Suche markiert Treffer und verändert die Ansicht nicht; sie zählt nicht in „X von Y Zeilen“ und durchsucht nur sichtbare Spalten. Begründung: ADR 0002. Wer sie später doch filtern lässt, muss Statuszeile, Zähler und ADR gemeinsam ändern.
- **Treffer:** `SearchHits.cells` enthält Zellmasken für alle sichtbaren Spalten, aber nur in Zeilen, die alle Begriffe enthalten (`cell_any & row_all`). Nicht-Treffer-Zeilen werden nicht markiert, auch wenn dort ein einzelner Begriff vorkommt. Der Zähler zählt Zeilen, nicht Zellen.
- **Suchhintergrund:** `_SearchTask` bekommt eine Generation und ein `threading.Event`. Ergebnisse mit alter Generation werden ignoriert; beim neuen Tippen wird das Event gesetzt. `_start_search()` wird auch aus `_restart_search()` direkt aufgerufen (ohne 200-ms-Wartezeit), damit Filter-/Sortieränderungen sofort neu rechnen.
- **Suche bei Änderungen:** `_apply_view()` baut ein neues Modell, setzt `_hits` zurück und ruft `_restart_search()`. `set_column_visible()` und `show_all_columns()` rufen es ebenfalls. `_reset_search()` blockiert beim Leeren die Signale, sonst würde das Leeren eine neue Suche starten.
- **Splash:** `create_splash()` liefert `SplashScreen`, eine Unterklasse, die `mousePressEvent` ignoriert; ein normales `QSplashScreen` würde sich per Klick schließen. Splash nur in `app.main` erzeugen, nicht in `MainWindow` – sonst erscheint er in jedem GUI-Test. `SPLASH_MIN_MS = 800`; `test_startup.py` ersetzt `QApplication`, `MainWindow` und `create_splash` und prüft die Reihenfolge.
- **Icon:** als Paketdatum über `importlib.resources` laden, nicht relativ zum Arbeitsverzeichnis. `tools/make_icon.py` muss ohne zusätzliche Bildbibliothek laufen; `test_icon.py` prüft die sieben Größen und dass die Datei byte-gleich zum Generator ist.
- **Version:** genau eine Quelle, `csv_dis.__version__`; `pyproject.toml` liest sie über `attr`. Nach Änderungen `pip install -e ".[dev]"` erneut ausführen, sonst bleibt die Metadatenversion alt.
- **Qt-Version im „Über“-Dialog:** `qVersion()` liefert die installierte Laufzeit (6.11.2), `QT_VERSION_STR` die Build-Version von PyQt6 (6.11.0). Für „installierte Version“ ist `qVersion()` richtig.
- **Lizenz:** PyQt6 6.11.0 ist GPL-3.0-only, Qt LGPLv3, Polars MIT, Python PSF. Die App steht deshalb unter GPLv3 (Copyright Ralf Joswig); bei Weitergabe müssen Quellcode, `LICENSE` und `THIRD-PARTY-NOTICES.md` mit.
- **Falsches Encoding:** Ein erzwungenes UTF-8 auf einer Windows-1252-Datei führt zu `CsvLoadError`; die bisherige Ansicht bleibt erhalten, weil `_apply_loaded` nur bei Erfolg läuft.
- **Filter pro Spalte:** `set_filter` ersetzt einen bestehenden Filter derselben Spalte. Die Filterleiste hat daher höchstens einen Eintrag pro Spalte.
- **Modell:** `CsvTableModel` bekommt die gefilterte/sortierte Ansicht; Ausblenden läuft über `QTableView.setColumnHidden`, nicht über Entfernen der Spalte. Nach jedem neuen Modell werden die ausgeblendeten Spalten erneut gesetzt. Treffer-Hintergründe kommen aus `BackgroundRole`, die dunkle Schrift auf Trefferzellen aus `ForegroundRole`; `set_search_hits()` repaintet die ganze Tabelle, `set_current_row()` nur die betroffenen Zeilen.
- **Sortierung im View:** `setSortingEnabled(False)` bleibt bewusst; die Sortierung macht Polars, nicht `QSortFilterProxyModel`.
- **Taskleiste:** Bei ungepackten Python-Programmen nimmt Windows das Icon des Host-Prozesses (`python.exe`) für die Taskleiste, auch wenn `setWindowIcon`, `WM_SETICON`, das Klassen-Icon (`SetClassLongPtr`) und eine eigene AppUserModelID gesetzt sind – alles am 2026-10-26 erfolglos probiert. Erst die PyInstaller-`.exe` mit `--icon` zeigt das csv-dis-Icon. Diesen Umweg nicht erneut versuchen.
- **PyInstaller:** Das Startskript muss absolute Importe nutzen (`tools/launcher.py`); `src/csv_dis/__main__.py` mit relativen Importen funktioniert als PyInstaller-Einstieg nicht. `--paths src` ist nötig, damit die Analyse das Paket findet. Das Icon zusätzlich als `--add-data` mitnehmen, sonst findet `importlib.resources` es in der `.exe` nicht.
- **Build:** `--clean` löscht `build/`; `dist/csv-dis/` (158 Dateien, 251,5 MB) muss als Ganzes weitergegeben werden, nicht nur die `.exe`. Die Tests prüfen die `.exe` nur, wenn sie existiert; `pytest` baut nicht selbst, ein veralteter Build bleibt also unentdeckt.
- Die Drag-&-Drop-Geste wurde am 2026-10-26 von Hand geprüft; zusätzlich existieren synthetische Qt-Tests.
- Beispieldateien liegen außerhalb des Projekts und können persönliche Daten enthalten: nicht kopieren.
- Keine Git-Befehle oder Commits voraussetzen.

## Dateien

| Pfad | Rolle |
|---|---|
| `pyproject.toml` | Abhängigkeiten, dynamische Version, Paketdaten, pytest-Einstellungen |
| `src/csv_dis/__init__.py` | einzige Versionsquelle `__version__` |
| `src/csv_dis/__main__.py` | Start über `python -m csv_dis` |
| `src/csv_dis/csv_loader.py` | Parser, Encoding, Trennzeichen |
| `src/csv_dis/column_types.py` | Erkennung Zahl/Datum/Text |
| `src/csv_dis/query.py` | Filterausdrücke, UND-Verknüpfung, Sortierung |
| `src/csv_dis/search.py` | Trefferlogik ohne GUI (`SearchHits`, `search_frame`) |
| `src/csv_dis/search_bar.py` | Suchfeld, Zähler, „Zurück“/„Weiter“, Tasten |
| `src/csv_dis/model.py` | `QAbstractTableModel` über Polars, Treffer-Hintergründe |
| `src/csv_dis/header.py` | Kopfzeile mit Filtersymbol |
| `src/csv_dis/filter_dialog.py` | Filter-Popup mit Validierung |
| `src/csv_dis/parser_dialog.py` | Dialog für Trennzeichen und Encoding |
| `src/csv_dis/about_dialog.py` | „Über csv-dis“ mit Lizenz und Bibliotheken |
| `src/csv_dis/resources.py` | Icon aus Paketdaten laden |
| `src/csv_dis/splash.py` | Splash-Bild und klickfester Splash |
| `src/csv_dis/main_window.py` | Fenster, Datei, Filterleiste, Suche, Live-Abfrage |
| `src/csv_dis/app.py` | Einstiegspunkt mit Icon und Splash |
| `src/csv_dis/assets/csv-dis.ico` | Programm-Icon, 16–256 px |
| `LICENSE` | GPLv3-Volltext |
| `THIRD-PARTY-NOTICES.md` | Drittlizenztexte (Qt, Python, Polars) |
| `docs/v2-spec.md` | Umfang und Abnahme v2 |
| `docs/adr/0002-suche-markiert-statt-zu-filtern.md` | Warum die Suche nicht filtert |
| `tests/test_csv_loader.py` | 19 Parser-Tests |
| `tests/test_column_types.py` | 7 Typ-Tests |
| `tests/test_query.py` | 13 Abfrage-Tests |
| `tests/test_search.py` | 12 Tests der Trefferlogik |
| `tests/test_gui_smoke.py` | 5 GUI- und Drop-Tests |
| `tests/test_gui_loading.py` | 5 Tests für Hintergrundladen und Abbruch |
| `tests/test_gui_parser.py` | 6 Tests für Trennzeichen-/Encoding-Korrektur |
| `tests/test_gui_query.py` | 10 GUI-Tests für Filter, Sortierung, Spalten |
| `tests/test_gui_search.py` | 18 GUI-Tests für Suchleiste, Markierung, Navigation, Zustand |
| `tests/test_about.py` | 5 Tests für den „Über“-Dialog |
| `tests/test_icon.py` | 3 Tests für ICO-Größen, Ladbarkeit, Reproduzierbarkeit |
| `tests/test_splash.py` | 5 Tests für Mindestdauer, Bild, Version, Klickfestigkeit |
| `tests/test_startup.py` | 1 Test für Splash vor dem Dateiöffnen |
| `tests/test_version.py` | 4 Tests für Version und Lizenzdateien |
| `tests/test_packaging.py` | 7 Tests für Build-Parameter, App-ID und gebaute `.exe` |
| `tests/conftest.py` | Qt-Fixtures, `QT_QPA_PLATFORM=offscreen` |
| `tools/make_large_csv.py` | Generator großer Testdateien |
| `tools/make_icon.py` | Reproduzierbarer ICO-Generator |
| `tools/build_exe.py` | PyInstaller-Build nach `dist/csv-dis/` inkl. Lizenzkopie |
| `tools/launcher.py` | Einstiegsskript für den PyInstaller-Build |
| `dist/csv-dis/` | Gebaute Anwendung (`.exe`, Bibliotheken, Lizenztexte) |
| `docs/v1-spec.md` | Sollverhalten und Abnahme v1 |
| `CONTEXT.md` | Begriffe |
| `docs/adr/0001-polars-datenmodell.md` | Datenmodell-Entscheidung |
