# Suche markiert, statt zu filtern

## Kontext

v1 filtert pro Spalte: Eine Bedingung schließt Zeilen aus, mehrere Filter sind UND-verknüpft, die Statuszeile zählt die verbleibenden Zeilen. Beim Nachschlagen ist die gesuchte Zeile oft bekannt, die Spalte aber nicht. Eine spaltenübergreifende Suche muss deshalb etwas anderes leisten als ein Filter.

Drei Wege waren denkbar: Die Suche verengt die Ansicht auf Treffer, sie markiert Treffer in der unveränderten Ansicht, oder ein Umschalter bietet beides.

## Entscheidung

Die Suche markiert ihre Treffer und verändert die Ansicht nicht. Ein Treffer ist eine Zeile, in der jeder Suchbegriff mindestens einmal in einer sichtbaren Spalte vorkommt; mehrere Begriffe sind UND-verknüpft. „Weiter“ und „Zurück“ springen zeilenweise, alle passenden Zellen werden markiert.

## Alternativen

- **Ansicht auf Treffer verengen:** Treffer wären isoliert und leicht zu zählen, aber der Kontext ginge verloren und die Statuszeile müsste zwischen Filter- und Suchzeilen unterscheiden. Zudem würde die Suche mit dem bestehenden Filterbegriff um dieselbe Bedeutung konkurrieren.
- **Umschalter „nur Treffer“:** vereinigt beide Verhaltensweisen, verlangt aber zwei Modi, einen zusätzlichen Zustand und eine Erklärung, wann welcher Modus gilt.
- **Treffer pro Zelle statt pro Zeile:** präziser beim Markieren, aber „Weiter“ würde durch viele Zellen derselben Zeile springen und das Finden der Zeile verlangsamen.

## Konsequenzen

- Die Statuszeile bleibt allein den Filtern vorbehalten; die Suche hat einen eigenen Trefferzähler.
- Ausgeblendete Spalten sind nicht durchsuchbar, weil jeder Treffer sichtbar und anspringbar bleiben muss. Die Oberfläche muss das über den Platzhaltertext klarstellen.
- Ändern sich Filter, Sortierung oder Spalten, muss die Suche auf der neuen Ansicht neu laufen; der Suchtext bleibt dabei erhalten.
- Wer erwartet, dass eine Suche filtert, wird überrascht. Trefferzähler und Markierung müssen das Verhalten unmissverständlich zeigen.
- Die Suche braucht einen eigenen Hintergrundlauf mit Abbruch, weil sie bei 1 Mio. Zeilen nicht im GUI-Thread rechnen darf.
