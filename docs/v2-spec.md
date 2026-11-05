# v2 – Suche, Version, „Über“, Icon, Splash und Paketierung

Stand: 2026-10-26

Schließt an `docs/v1-spec.md` an. v1 ist abgenommen; dieses Dokument legt ausschließlich den nächsten Increment fest.

## Ziel

Eine Zeile in einer großen Datei schnell finden, ohne die Ansicht zu verengen. Dazu eine nachvollziehbare Versionsnummer, ein „Über“-Dialog mit Version, Lizenz und Laufzeitbibliotheken sowie ein Programm-Icon, ein Splash-Screen beim Start und eine gepackte Windows-Anwendung, die auch in der Taskleiste das eigene Icon zeigt.

## Nicht-Ziele

- Die Suche verändert die Ansicht nicht; sie ist kein Filter.
- Keine regulären Ausdrücke, keine Unscharfsuche, keine Suchhistorie, keine gespeicherte Suche.
- Keine Suche in ausgeblendeten Spalten und kein Hinweis auf Treffer dort.
- Kein Export, keine Bearbeitung, keine Mehrfachdateien, keine Auswertung.
- Keine vollständigen Lizenztexte im Dialog; sie liegen als Dateien bei.

## Suche

- Dauerhafte Suchleiste zwischen Filterleiste und Tabelle. Sie ist immer sichtbar, auch ohne aktive Suche.
- Inhalt: Suchfeld mit Platzhalter „Sichtbare Spalten durchsuchen…“, Trefferzähler, „Zurück“ und „Weiter“.
- `Strg+F` setzt den Fokus ins Suchfeld, `Esc` leert es und entfernt alle Markierungen.
- Die Eingabe wird an Leerzeichen in Begriffe zerlegt; führende, folgende und mehrfache Leerzeichen zählen nicht.
- Eine **Zeile** ist Treffer, wenn jeder Begriff mindestens einmal in einer ihrer sichtbaren Zellen vorkommt – auch verteilt auf verschiedene Spalten.
- Vergleich: Teilstring, Groß-/Kleinschreibung egal, literal. Umlaute werden nicht vereinfacht (`ä` ≠ `a`), wie beim Textfilter.
- Durchsucht werden nur die sichtbaren Spalten der aktuellen Ansicht, in ihrer aktuellen Reihenfolge.
- Alle passenden Zellen werden markiert; der aktuelle Treffer wird deutlicher markiert.
- „Weiter“ springt zum nächsten Treffer, „Zurück“ zum vorherigen; am Ende geht es am Anfang weiter (Umlauf). `Enter` = weiter, `Umschalt+Enter` = zurück.
- Beim Anspringen wird die Zeile sichtbar gemacht und waagerecht zur ersten passenden Zelle gescrollt.
- Trefferzähler: „X von Y Treffern“; ohne Treffer „0 Treffer“; ohne Suche bleibt er leer.
- Eine leere oder nur aus Leerzeichen bestehende Eingabe ist keine Suche.
- Filter, Sortierung und ausgeblendete Spalten dürfen sich ändern, während eine Suche aktiv ist: Der Suchtext bleibt, die Treffer werden auf der neuen Ansicht neu berechnet, der aktuelle Treffer wird der erste.
- Neues Öffnen einer Datei und Neuladen über den Parser-Dialog leeren die Suche.
- Die Statuszeile bleibt unverändert; die Suche zählt nicht in „X von Y Zeilen“.
- Die Berechnung läuft 200 ms nach der letzten Eingabe im Hintergrund; eine neue Eingabe bricht die laufende Berechnung ab, veraltete Ergebnisse werden verworfen. Das Fenster bleibt bedienbar.

## Version

- Die Version steht genau einmal: `__version__` in `src/csv_dis/__init__.py`. `pyproject.toml` liest sie dynamisch über `attr`.
- Der abgenommene v1-Stand ist **1.0.0**, dieser Increment wird **1.1.0**.
- „v2“ ist der Name des Increments, nicht die Softwareversion.
- Die Version erscheint nicht im Fenstertitel und nicht in der Statuszeile.

## „Über“-Dialog

- Erreichbar über **Hilfe > Über csv-dis**.
- Zeigt:
  - Name und Version: `csv-dis 1.1.0`
  - Copyright: `Copyright (C) 2026 Ralf Joswig`
  - Lizenz der App: GPLv3 als Kurzangabe mit Verweis auf `LICENSE`
  - Tabelle der Laufzeitbibliotheken mit installierter Version und Lizenz:
    - Python – PSF-Lizenz
    - PyQt6 – GPL-3.0-only
    - Qt – LGPLv3
    - Polars – MIT
  - Verweis auf `THIRD-PARTY-NOTICES.md` für die vollständigen Drittlizenztexte.
- Versionen werden zur Laufzeit gelesen, nicht fest eingetragen.
- Der Dialog ist modal und schließt mit „OK“.

## Icon und Splash-Screen

- Die App bekommt ein eigenes Programm-Icon als `.ico` mit den Größen 16, 24, 32, 48, 64, 128 und 256 px.
- Das Motiv wird im Projekt erzeugt: ein schlichtes Tabellenraster mit Trichter, ohne externe Design-Datei. Ein kleines Skript `tools/make_icon.py` erzeugt die `.ico`-Datei reproduzierbar.
- Das Icon wird über `QApplication.setWindowIcon` gesetzt und erscheint in Titelleiste, Taskleiste und im „Über“-Dialog.
- Die Icon-Datei liegt im Paket unter `src/csv_dis/assets/` und wird als Paketdaten mitgeliefert; der Pfad wird zur Laufzeit über `importlib.resources` aufgelöst, nicht relativ zum Arbeitsverzeichnis.
- Die Taskleiste zeigt unter Windows nur bei der gepackten `.exe` zuverlässig das eigene Icon; beim Start über `python -m csv_dis` gilt das Python-Host-Icon. Deshalb gehört die Paketierung (siehe unten) zum Umfang.
- Beim Start zeigt ein Splash-Screen das Icon, den Namen `csv-dis` und die Version.
- Der Splash verschwindet von selbst, sobald das Hauptfenster bereit ist; er verlangt keine Eingabe und lässt sich nicht per Klick schließen.
- Er bleibt mindestens 800 ms sichtbar, damit er bei schnellem Start nicht nur kurz aufblitzt.
- Beim Öffnen einer Datei über die Kommandozeile erscheint danach der vorhandene Lade-Fortschrittsdialog; Splash und Fortschrittsdialog überlagern sich nicht.
- Beim Öffnen weiterer Dateien im laufenden Programm erscheint kein Splash.
- Keine Animation, kein Ton, keine Verzögerung des Ladens über die Mindestdauer hinaus.

## Paketierung

- `tools/build_exe.py` baut mit PyInstaller eine eigenständige Windows-Anwendung nach `dist/csv-dis/csv-dis.exe`.
- Das Icon wird in die `.exe` eingebettet (`--icon`) und zusätzlich als Paketdatum mitgenommen, damit `importlib.resources` es zur Laufzeit findet.
- Der Build läuft ohne Konsolenfenster (`--windowed`); Start, Splash, Dateiöffnen und Suche verhalten sich wie beim Start über `python -m csv_dis`.
- Beim Start setzt die App unter Windows eine eigene AppUserModelID (`RalfJoswig.csv-dis`), damit Taskleiste und Fenster zusammengehalten werden.
- `LICENSE` und `THIRD-PARTY-NOTICES.md` werden mit in den Build-Ordner kopiert, damit die Weitergabe vollständig ist.
- Der Build ist ein Entwicklerschritt, kein Teil von `pytest`; die Tests prüfen die Build-Parameter und – falls vorhanden – die gebaute `.exe` (GUI-Subsystem, Icon-Ressource).
- PyInstaller ist Entwicklungsabhängigkeit in `pyproject.toml`, nicht Laufzeitabhängigkeit.

## Lizenz

- Die App steht unter **GPLv3**, weil das verwendete PyQt6 GPL-3.0-only ist und eine Weitergabe geplant ist.
- `LICENSE` enthält den vollständigen GPLv3-Text.
- `THIRD-PARTY-NOTICES.md` enthält PyQt6 (GPL-3.0-only), Qt (LGPLv3), Polars (MIT) und Python (PSF).
- Bei einer Weitergabe werden Quellcode und Lizenzdateien mitgeliefert.
- Entwicklungswerkzeuge wie pytest erscheinen nicht im „Über“-Dialog und nicht in den Drittlizenztexten.

## Abnahme

1. In beiden Beispieldateien eine bekannte Zeile über eine Spalte hinweg suchen: Treffer wird markiert, der Zähler stimmt, „Weiter“/„Zurück“ laufen um.
2. Zwei Begriffe, die in verschiedenen sichtbaren Spalten derselben Zeile stehen, ergeben genau einen Treffer.
3. `Strg+F`, `Esc`, `Enter` und `Umschalt+Enter` verhalten sich wie beschrieben.
4. Filter ändern, Sortierung wechseln, Spalte ausblenden: Die Suche bleibt aktiv und liefert neu berechnete Treffer; eine andere Datei öffnen leert sie.
5. Ein Wert in einer ausgeblendeten Spalte erzeugt keinen Treffer und keinen Hinweis.
6. 1-Mio.-Zeilen-Datei: Die Eingabe blockiert das Fenster nicht; der gemessene Wert wird in `STATUS.md` dokumentiert.
7. „Über csv-dis“ zeigt 1.1.0, Ralf Joswig, GPLv3 und die vier Laufzeitbibliotheken mit ihren tatsächlich installierten Versionen.
8. `pytest` ist grün; die Version aus `csv_dis.__version__` stimmt mit der Paketmetadaten-Version überein.
9. Das Icon ist in Titelleiste und Taskleiste sichtbar und erscheint auch im „Über“-Dialog.
10. Der Splash-Screen zeigt beim Start Icon, Namen und Version, verschwindet von selbst und blockiert die Bedienung nicht; bei Start mit Datei folgt danach der Lade-Fortschrittsdialog.
11. `dist/csv-dis/csv-dis.exe` startet mit Splash, öffnet eine Datei, zeigt in der Taskleiste das csv-dis-Icon und durchsucht die Tabelle; `LICENSE` und `THIRD-PARTY-NOTICES.md` liegen daneben.

## Testdaten

Wie v1; die Dateien liegen außerhalb des Projekts und werden nicht kopiert:

- `C:\Users\ralfj\Coding\Netzwerk\docs\Geräteübersicht 20261025.csv`
- `C:\Users\ralfj\Coding\Schreibtisch\datenblaetter\_produktliste.csv`
- große Datei über `tools\make_large_csv.py`
