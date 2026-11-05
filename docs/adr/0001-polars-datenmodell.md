# Polars als Datenmodell für Dateien bis 100 MB

## Kontext

v1 muss eine CSV-Datei mit bis zu 1 Mio. Zeilen und etwa 100 MB öffnen, filtern und sortieren, während die PyQt6-Oberfläche bedienbar bleibt. Eine Liste von Python-Strings bräuchte bei 30 Spalten mehrere GB; pandas speichert Textspalten ebenfalls als Python-Objekte.

## Entscheidung

Die Datei wird vollständig in einen Polars-DataFrame geladen. Die Tabelle zeigt ihn über ein virtualisiertes `QAbstractTableModel`; Filtern und Sortieren laufen in Polars in einem Hintergrund-Thread. Angezeigt wird immer der Originaltext; der erkannte Spaltentyp dient nur Sortierung und Filter.

## Alternativen

- **pandas**: vertrauter, aber deutlich höherer Speicherbedarf bei vielen Textspalten.
- **SQLite (temporär)**: speicherschonend und ohne Zusatzabhängigkeit, widerspricht aber der Grenze „keine Datenbank“ und verlagert Typerkennung sowie Spaltensichtbarkeit in SQL.
- **Standardbibliothek**: bei 1 Mio. × 30 Spalten nicht tragfähig.

## Konsequenzen

- Zusätzliche Laufzeit- und Packaging-Abhängigkeit.
- Trennzeichen- und Encoding-Erkennung sowie das Auffüllen unvollständiger Zeilen bleiben Aufgabe des Programms.
