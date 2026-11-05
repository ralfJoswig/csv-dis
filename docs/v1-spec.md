# v1-Spezifikation

Stand: 2026-10-26. Abgestimmt im Grilling; Grundlage für `STATUS.md` und `TODO.md`.

Technik: Python ≥ 3.12, PyQt6, Polars 2.x, Tests mit pytest.

## Ziel

`csv-dis` zeigt genau eine CSV-Datei in einem lokalen Windows-Fenster als Tabelle. Der Benutzer kann Zeilen filtern, nach einer Spalte sortieren und Spalten ausblenden. Die Datei wird nie verändert.

## Nicht-Ziele

- Bearbeiten oder Speichern der Datei
- Export der Ansicht (CSV, Excel, PDF)
- Server, Datenbank, Benutzerverwaltung
- Mehrere Dateien gleichzeitig oder Dateivergleich
- Gruppieren, Summieren, Kennzahlen, Diagramme, Formeln
- Verpackung als EXE; v1 läuft aus der Entwicklungsumgebung (in v2 nachgeholt, siehe `docs/v2-spec.md`)

## Eingabe

- Datei öffnen per Dialog oder durch Ablegen einer lokalen Datei auf dem Fenster.
- Drag & Drop akzeptiert nur lokale Dateien, keine URLs und keine Ordner. Bei mehreren abgelegten Dateien wird die erste geöffnet und ein Hinweis angezeigt.
- Eine Datei pro Fenster; Öffnen einer anderen Datei ersetzt die aktuelle Ansicht.
- Parser:
  - BOM am Dateianfang entfernen.
  - UTF-8 strikt; bei ungültigen Bytes Windows-1252 mit sichtbarer Warnung.
  - Trennzeichen aus `;` `,` Tab `|` anhand der ersten nicht leeren Zeilen außerhalb von Anführungszeichen erkennen; die Feldanzahl der Kopfzeile ist der Anker, unregelmäßige Datenzeilen dürfen die Erkennung nicht verhindern.
  - Erste Zeile ist immer die Kopfzeile.
  - Anführungszeichen nach RFC 4180, inklusive Trennzeichen und Zeilenumbrüchen in Feldern.
  - Zu kurze Zeilen mit leeren Zellen auffüllen; überzählige Felder verwerfen und melden.
  - Leere Spaltennamen als `Spalte N` (1-basierter Index), doppelte als `Name (2)` eindeutig machen.
  - Trennzeichen und Encoding können nach dem Öffnen manuell korrigiert werden; die Datei wird dann neu geladen.
- Nicht lesbare Datei: Fehlerdialog, kein halb gefülltes Fenster.

## Spaltentypen

Der Typ wird aus allen nicht leeren Werten einer Spalte abgeleitet:

- **Zahl**: optionales Vorzeichen, Ziffern, optional ein Dezimalpunkt. Führende Nullen oder Einheiten (`432 Mbit/s`) ⇒ Text.
- **Datum**: ausschließlich ISO `YYYY-MM-DD` oder `YYYY-MM-DD HH:MM[:SS]`.
- **Text**: alles andere, auch gemischte Spalten und Spalten ohne Werte.

Der Originaltext wird immer unverändert angezeigt. Der Typ beeinflusst nur Sortierung und Filteroperatoren.

## Ansicht und Bedienung

- Tabelle mit virtualisiertem Modell; nur sichtbare Zeilen werden gerendert.
- Kopfzeile: Klick sortiert aufsteigend, erneuter Klick absteigend. Genau eine Sortierspalte.
- Leere Zellen stehen beim Sortieren in beiden Richtungen am Ende.
- Filtersymbol im Spaltenkopf öffnet ein Popup mit Operator und Wert für diese Spalte.
  - Text: enthält, ist gleich, ist ungleich, ist leer, ist nicht leer (Groß-/Kleinschreibung egal).
  - Zahl: =, ≠, <, ≤, >, ≥, ist leer, ist nicht leer.
  - Datum: =, vor, nach, ist leer, ist nicht leer.
- Pro Spalte ist höchstens ein Filter aktiv; ein neuer Filter ersetzt den bisherigen.
- Mehrere aktive Filter sind UND-verknüpft. Die Filterleiste über der Tabelle zeigt sie als entfernbare Einträge, inklusive „Alle entfernen“.
- Ungültige Filtereingaben werden markiert und nicht angewendet.
- Spalten lassen sich per Kopfmenü aus- und einblenden. Es darf auch alles ausgeblendet werden; dann erscheint ein Hinweis.
- Statuszeile: „X von Y Zeilen“.
- Filter und Sortierung wirken live nach etwa 200 ms; die Berechnung läuft im Hintergrund und eine neue Eingabe bricht die laufende ab.
- Das Fenster bleibt beim Öffnen, Filtern und Sortieren bedienbar; für das Öffnen gibt es eine Fortschrittsanzeige.
- Kein Zustand wird gespeichert: Nach einem Neustart ist keine Datei geöffnet und kein Filter aktiv.
- Oberfläche auf Deutsch.

## Abnahme v1

1. Beide vorhandenen Beispieldateien öffnen; alle Spalten und Werte stimmen, inklusive Umlauten und Anführungszeichen.
2. Eine synthetische Datei mit 1 Mio. Zeilen öffnen, filtern und sortieren, ohne dass das Fenster einfriert.
3. Eine Datei per Drag & Drop öffnen; eine URL und einen Ordner ablehnen; bei mehreren Dateien wird nur die erste geöffnet.
4. Mehrere Filter kombinieren, einzeln und gesamt entfernen; Spalten aus- und einblenden; Sortierrichtung wechseln.
5. Neu starten: keine Datei, kein Filter, keine ausgeblendete Spalte aus der vorigen Sitzung.

### Testdaten

Zwei lokale Beispieldateien außerhalb des Projekts; nicht kopieren, sie können persönliche Daten enthalten:

- `C:\Users\ralfj\Coding\Netzwerk\docs\Geräteübersicht 20261025.csv` – Semikolon, UTF-8 mit BOM
- `C:\Users\ralfj\Coding\Schreibtisch\datenblaetter\_produktliste.csv` – Komma, UTF-8 mit BOM, Anführungszeichen
- Große Testdatei: `.\.venv\Scripts\python.exe tools\make_large_csv.py --rows 1000000` (Standardziel im temporären Verzeichnis)
