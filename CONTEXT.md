# csv-dis

Ein lokales Windows-Programm, das eine CSV-Datei als Tabelle anzeigt. Es verändert die Datei nicht; alle Eingriffe betreffen nur die Ansicht.

## Sprache

**Datei**:
Die geöffnete CSV-Datei mit allen Zeilen und Spalten, so wie sie auf der Platte steht.
_Avoid_: Datensatz, Quelle, Dokument

**Ansicht**:
Die Teilmenge der Datei, die nach Filter, Sortierung und ausgeblendeten Spalten in der Tabelle erscheint.
_Avoid_: Tabelle, Ergebnis, Auswertung

**Zeile**:
Ein Datensatz der Datei.
_Avoid_: Eintrag, Record, Datensatz

**Spalte**:
Eine Spalte der Datei mit Kopfzeile und erkanntem Spaltentyp.
_Avoid_: Feld, Kolumne

**Kopfzeile**:
Die erste Zeile der Datei. Ihre Werte sind die Spaltennamen und werden immer als Kopf behandelt, nie als Daten.
_Avoid_: Header, Titelzeile

**Leere Zelle**:
Ein Feld ohne Inhalt; es zählt bei der Typerkennung nicht mit.
_Avoid_: NULL, null, leerer Wert

**Erkannter Spaltentyp**:
Der Typ, den das Programm aus den Werten einer Spalte ableitet: Zahl, Datum oder Text. Er ist nicht der Anzeigetext.
_Avoid_: Datentyp, Format

**Filter**:
Eine Bedingung auf genau einer Spalte, die Zeilen ein- oder ausschließt. Pro Spalte ist höchstens ein Filter aktiv; ein neuer Filter ersetzt den bisherigen.
_Avoid_: Suche, Abfrage, Query

**Suche**:
Eine Textsuche über alle sichtbaren Spalten der Ansicht. Sie verändert die Ansicht nicht, sondern markiert ihre Treffer.
_Avoid_: Suchfilter, globale Abfrage

**Treffer**:
Eine Zeile der Ansicht, in der jeder Begriff der Suche mindestens einmal vorkommt – auch in verschiedenen Spalten.
_Avoid_: Fundstelle, Match

**Filtersymbol**:
Das Trichter-Symbol im Kopf einer Spalte. Ein Klick darauf öffnet den Filter für diese Spalte.
_Avoid_: Filterknopf, Icon

**Sortierung**:
Die Reihenfolge der Zeilen in der Ansicht, bestimmt durch genau eine Spalte und eine Richtung.
_Avoid_: Ordnung, Ranking

**Ausblenden**:
Eine Spalte aus der Ansicht entfernen, ohne Datei oder Daten zu verändern.
_Avoid_: Löschen, Entfernen, Filtern
