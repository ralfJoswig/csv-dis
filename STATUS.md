# Status

Stand: 2026-11-05

Ausführliche Übergabe für die nächste Sitzung: `HANDOFF.md`.

## Ziel

Lokales Windows-Programm zur Anzeige **einer** CSV-Datei mit Filtern, Sortierung, ausblendbaren Spalten und spaltenübergreifender Suche. Read-only. v1: `docs/v1-spec.md`; v2: `docs/v2-spec.md`.

## Aktuell

- Versionierung: Git-Repository auf Branch `main`, Remote `origin` → https://github.com/ralfJoswig/csv-dis, Stand von 1.1.0 gepusht (2026-11-05). `.gitignore` schließt `.venv/`, `build/`, `dist/` sowie die lokalen Startskripte `csv_dis.cmd` und `start.cmd` aus.
- Grundgerüst steht: `pyproject.toml`, `src/csv_dis`, lokale `.venv`, pytest.
- CSV-Laden funktioniert: BOM, UTF-8/Windows-1252, Trennzeichen `; , Tab |`, RFC 4180 inklusive mehrzeiliger Felder, Kopfzeilen-Normalisierung, kurze Zeilen auffüllen, lange melden.
- Öffnen läuft im Hintergrund: unbestimmte Fortschrittsanzeige mit „Abbrechen“, Fenster bleibt bedienbar. Eine neu geöffnete Datei ersetzt den laufenden Ladevorgang; veraltete Ergebnisse werden verworfen.
- Parser-Korrektur: „Datei > Trennzeichen und Encoding…“ öffnet einen Dialog mit den aktuellen Werten; „Neu laden“ lädt die Datei mit der Auswahl neu. Filter, Sortierung, ausgeblendete Spalten und Suche werden dabei zurückgesetzt. Schlägt das Neuladen fehl, bleibt die bisherige Ansicht erhalten.
- Spaltentypen: `column_types.py` erkennt Zahl, Datum und Text aus allen nicht leeren Werten. Führende Nullen und Einheiten gelten als Text; Datum nur als `YYYY-MM-DD` oder `YYYY-MM-DD HH:MM[:SS]` mit gültigem Kalender. Angezeigt wird weiterhin der Originaltext.
- Filter: `query.py` baut Polars-Ausdrücke; mehrere Filter sind UND-verknüpft, der geladene DataFrame bleibt unverändert. Pro Spalte ist ein Filter aktiv, ein neuer ersetzt den bisherigen.
- Oberfläche: Trichter-Symbol im Spaltenkopf (Klick öffnet den Filterdialog), Doppelklick auf den Kopf und Kopfmenü als weitere Wege; Filterleiste mit entfernbaren Einträgen und „Alle entfernen“; ungültige Werte werden im Dialog markiert und nicht angewendet.
- Sortierung: Klick auf den Kopf sortiert aufsteigend, erneuter Klick absteigend; genau eine Spalte; leere Zellen stehen in beiden Richtungen am Ende; Zahl, Datum und Text werden typgerecht sortiert.
- Spalten lassen sich über das Kopfmenü aus- und einblenden, auch alle; die Statuszeile zeigt dann einen Hinweis. „Ansicht > Alle Spalten einblenden“ stellt alles wieder her.
- Statuszeile: „X von Y Zeilen“ plus Trennzeichen und Encoding; die Suche zählt dort nicht mit.
- Filter und Sortierung wirken live nach 200 ms im Hintergrund-Thread; neue Eingaben brechen die laufende Berechnung ab, veraltete Ergebnisse werden verworfen.
- Suche (`search.py`, `search_bar.py`, `model.py`, `main_window.py`): dauerhafte Leiste zwischen Filterleiste und Tabelle, Platzhalter „Sichtbare Spalten durchsuchen…“, Trefferzähler, „Zurück“/„Weiter“.
- Trefferlogik: Eingabe wird an Leerzeichen in Begriffe zerlegt; eine Zeile ist Treffer, wenn jeder Begriff mindestens einmal in einer sichtbaren Zelle vorkommt. Teilstring, case-insensitiv, literal; Umlaute werden nicht vereinfacht. Ausgeblendete Spalten zählen nicht.
- Markierung: alle passenden Zellen der Trefferzeilen werden gelb hinterlegt, der aktuelle Treffer kräftiger. Navigation per „Weiter“/„Zurück“, `Enter`/`Umschalt+Enter`, mit Umlauf; die Zielzeile wird sichtbar gemacht und waagerecht zur ersten passenden Zelle gescrollt.
- `Strg+F` fokussiert das Suchfeld, `Esc` leert es und entfernt die Markierungen. Die Suche läuft 200 ms nach der letzten Eingabe im Hintergrund; eine neue Eingabe bricht sie ab.
- Bei Filter-, Sortier- und Spaltenänderungen bleibt der Suchtext erhalten und die Treffer werden auf der neuen Ansicht neu berechnet. Neues Öffnen und Parser-Neuladen leeren die Suche.
- Version: genau eine Quelle, `csv_dis.__version__ = "1.1.0"`; `pyproject.toml` liest sie dynamisch über `attr`. Die installierte Paketversion ist 1.1.0.
- „Hilfe > Über csv-dis“ (`about_dialog.py`): Name und Version, Copyright Ralf Joswig, GPLv3-Kurzangabe mit Verweis auf `LICENSE`, Tabelle der Laufzeitbibliotheken mit zur Laufzeit gelesenen Versionen und Verweis auf `THIRD-PARTY-NOTICES.md`.
- Lizenz: App GPLv3 wegen PyQt6 GPL-3.0-only. `LICENSE` enthält den vollständigen GPLv3-Text; `THIRD-PARTY-NOTICES.md` enthält PyQt6 (GPL-3.0-only), Qt (LGPLv3), Polars (MIT) und Python (PSF).
- Icon: `src/csv_dis/assets/csv-dis.ico` mit 16, 24, 32, 48, 64, 128 und 256 px, erzeugt von `tools/make_icon.py` (Tabellenraster mit Trichter). Wird über `importlib.resources` geladen und an App und Fenster gesetzt; im „Über“-Dialog sichtbar.
- Splash (`splash.py`, `app.py`): Icon, Name, Version und Untertitel auf dunkelblauem Bild, 420 × 230 px; mindestens 800 ms sichtbar, verschwindet selbstständig, ignoriert Klicks. Bei Start mit Datei wird die Datei erst nach dem Splash geöffnet, sodass der Lade-Fortschrittsdialog danach erscheint.
- Paketierung (`tools/build_exe.py`, `tools/launcher.py`): PyInstaller baut `dist/csv-dis/csv-dis.exe` ohne Konsolenfenster mit eingebettetem Icon und dem Icon als Paketdatum; `LICENSE` und `THIRD-PARTY-NOTICES.md` werden daneben kopiert. Der Build-Ordner ist 251,5 MB groß (158 Dateien), die `.exe` allein 4,1 MB; er ist vollständig weiterzugeben.
- Taskleiste: Die gepackte `.exe` zeigt in der Taskleiste das csv-dis-Icon (per Screenshot geprüft). Beim Start über `python -m csv_dis` zeigt Windows das Python-Host-Icon; das ist eine Eigenschaft ungepackter Skripte und der Grund für die Paketierung.
- AppUserModelID `RalfJoswig.csv-dis` wird beim Start unter Windows gesetzt (`app.py`), damit Fenster und Taskleisten-Schaltfläche zusammengehören.
- Tests: **120 grün**: 19 Loader, 5 GUI-Smoke, 5 GUI-Laden, 6 GUI-Parser, 7 Typen, 13 Abfrage, 10 GUI-Abfrage, 12 Suchlogik, 18 GUI-Suche, 5 „Über“, 3 Icon, 5 Splash, 1 Startablauf, 4 Version, 7 Paketierung. GUI offscreen.
- Messungen v1 (unverändert): 1 Mio. × 5 Spalten (50,1 MB) laden 0,11 s, Typen 0,20 s, Filter+Sortierung 0,02 s; 300.000 × 30 Spalten (118,1 MB) laden 0,18 s, Typen 0,34 s, Filter+Sortierung 0,01 s.
- Messung Suche mit derselben 1-Mio.-Datei: `search_frame` 46–129 ms je nach Begriff (1 Treffer: 99 ms, 3.999 Treffer: 96 ms, 1 Mio. Treffer: 46 ms). Im GUI-Pfad Ende-zu-Ende 310–328 ms inklusive 200 ms Eingabeverzögerung; während der Suche lief die Ereignisschleife weiter (23 Timer-Ticks à 10 ms), das Fenster blieb bedienbar.
- Beide Beispieldateien laden korrekt (46 × 29 und 209 × 3). Suche auf beiden geprüft: zwei Begriffe aus verschiedenen Spalten derselben Zeile ergeben genau einen Treffer; ein nicht vorhandener Begriff ergibt „0 Treffer“.

## Abnahme v1

Alle fünf Punkte aus `docs/v1-spec.md` am 2026-10-26 manuell mit positivem Ergebnis durchgeführt:

1. Beide Beispieldateien geöffnet: alle Spalten und Werte korrekt, inklusive Umlauten und Anführungszeichen.
2. 1-Mio.-Zeilen-Datei geöffnet, gefiltert und sortiert, ohne dass das Fenster einfriert.
3. Datei per echter Drag-&-Drop-Geste geöffnet; URL und Ordner abgelehnt; bei mehreren Dateien nur die erste geöffnet.
4. Mehrere Filter kombiniert, einzeln und gesamt entfernt; Spalten aus- und eingeblendet; Sortierrichtung gewechselt; Parser-Korrektur ausprobiert.
5. Neu gestartet: keine Datei, kein Filter, keine ausgeblendete Spalte aus der vorigen Sitzung.

**v1 ist damit abgenommen.**

## Abnahme v2

Am 2026-10-26 automatisiert und visuell geprüft:

1. Beide Beispieldateien: Suche nach zwei Begriffen aus derselben Zeile ergibt „1 von 1 Treffern“ mit Markierung. Navigation mit Umlauf ist mit zwei Treffern in den GUI-Tests abgedeckt.
2. Zwei Begriffe in verschiedenen sichtbaren Spalten derselben Zeile ergeben genau einen Treffer; ein Begriff ohne Vorkommen ergibt „0 Treffer“.
3. `Strg+F` fokussiert das Suchfeld; `Esc` leert die Suche; `Enter` und `Umschalt+Enter` navigieren. Alles mit echten Tastendrücken in den GUI-Tests.
4. Filter ändern, Sortierung wechseln, Spalte ausblenden: Suchtext und Treffer bleiben, werden neu berechnet. Andere Datei öffnen leert die Suche. Alles in GUI-Tests.
5. Ein Wert in einer ausgeblendeten Spalte erzeugt keinen Treffer (Unit- und GUI-Test).
6. 1-Mio.-Zeilen-Datei: Berechnung 46–129 ms, Ende-zu-Ende 310–328 ms inklusive 200 ms Verzögerung; die Ereignisschleife lief während der Suche weiter, das Fenster blockierte nicht.
7. „Über csv-dis“ zeigt im Screenshot: `csv-dis 1.1.0`, Copyright Ralf Joswig, GPLv3-Hinweis und die Bibliotheken Python 3.13.14, PyQt6 6.11.0, Qt 6.11.2, Polars 2.1.0 mit Lizenzen.
8. `pytest`: 120 grün; `csv_dis.__version__` = 1.1.0 = Paketmetadaten.
9. Icon: Titelleiste, „Über“-Dialog und die Taskleiste der gepackten `.exe` per Screenshot geprüft; alle sieben Größen sind im `.ico`. Beim Start über `python -m csv_dis` zeigt die Taskleiste das Python-Host-Icon.
10. Splash: Bild mit Icon, Name und Version visuell geprüft; Mindestdauer 800 ms im Starttest bestätigt; Datei öffnet erst nach dem Splash; Klicks schließen ihn nicht.
11. `dist/csv-dis/csv-dis.exe` gestartet: Splash nach 1,2 s sichtbar (420 × 230), Fenster mit Datei geöffnet (209 × 3 bzw. 46 × 29), Suchfeld per UI Automation auf `PC0-0-0-0` gesetzt → „1 von 1 Treffern“ mit markierter Zelle; Taskleiste zeigt das csv-dis-Icon; `LICENSE` und `THIRD-PARTY-NOTICES.md` liegen im Build-Ordner.

**v2 ist damit vollständig umgesetzt und abgenommen.**

## Start

```powershell
.\.venv\Scripts\python.exe -m csv_dis
```

Optional mit Datei:

```powershell
.\.venv\Scripts\python.exe -m csv_dis "C:\pfad\datei.csv"
```

Gepackt (mit eigenem Taskleisten-Icon):

```powershell
.\dist\csv-dis\csv-dis.exe
.\dist\csv-dis\csv-dis.exe "C:\pfad\datei.csv"
```

## Build

```powershell
.\.venv\Scripts\python.exe tools\build_exe.py
```

Ergebnis: `dist\csv-dis\` mit `csv-dis.exe`, `LICENSE` und `THIRD-PARTY-NOTICES.md`; Dauer etwa 1,5 Minuten.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Nächster Schritt

- v2 ist abgeschlossen. Für einen nächsten Increment zuerst `docs/v3-spec.md` anlegen (Ziel, Nicht-Ziele, Abnahme), dann umsetzen.
- Für spätere Änderungen: `docs/v2-spec.md`, ADR 0002 und die Suche-Tests gemeinsam pflegen.
