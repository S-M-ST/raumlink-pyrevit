# RaumLink Extension - Installation auf Terminalserver

## Was ist drin

`TestRaumLink.extension/` - pyRevit-Extension, die Raum-Info aus
verknuepften Architekturmodellen in Moebel-Elemente schreibt.

**Standalone:** Die Extension bringt ihre eigene kleine Shared-Parameter-Datei
mit (`RaumLink_SharedParams.txt`). Die zentrale Firmen-GGP wird nicht veraendert.

## Installation (3 Schritte)

### 1. Ordner kopieren

Kompletten Ordner `TestRaumLink.extension` an einen geeigneten Ort kopieren.
Empfehlung fuer Terminalserver:

```
C:\pyRevit-Extensions\TestRaumLink.extension
```

Alternativ an einen firmenweiten Netzlaufwerks-Pfad, der alle TS-User erreicht.

### 2. In pyRevit registrieren

Im Revit auf dem Terminalserver:

1. pyRevit-Tab oeffnen
2. `Settings` klicken
3. Bereich **"Custom Extension Directories"**
4. **Parent-Ordner** des `.extension`-Ordners hinzufuegen, also z.B.
   `C:\pyRevit-Extensions` (NICHT den .extension-Ordner selbst)
5. `Save Settings and Reload` klicken

Nach Reload erscheint der Tab **"RaumLink"** im Ribbon.

### 3. Benutzung je Projekt

Im jeweiligen Moebel-Projekt:

1. Tab **RaumLink** -> **SharedParams binden** (einmalig pro Projekt)
   - Bindet `117_100_111_Raumname_Link` + `117_100_112_Raumnr_Link`
     an Moebel + Moebelsysteme als Instance-Parameter
   - Nutzt die mitgelieferte `RaumLink_SharedParams.txt`
   - Die projekteigene SharedParametersFilename-Einstellung wird temporaer
     umgebogen und danach wieder zurueckgesetzt
2. Tab **RaumLink** -> **Raum aus Link**
   - Sammelt Raeume aus allen geladenen Architektur-Links
   - Schreibt Name + Nummer in die Moebel-Shared-Params

## Was tun wenn...

### ...die Params schon in eurer zentralen GGP existieren sollen

Einfach die 2 PARAM-Zeilen aus `RaumLink_SharedParams.txt` in die zentrale
GGP uebernehmen. Die Extension findet die Params trotzdem (GUIDs matchen).

### ...ihr andere Namen wollt

1. `RaumLink_SharedParams.txt` editieren (UTF-16 LE bewahren!)
2. Im Skript unter `ZIEL_PARAMS` (SharedParams.pushbutton/script.py) und
   `PARAM_RAUM_NAME` / `PARAM_RAUM_NUMMER` (RaumAusLink.pushbutton/script.py)
   die neuen Namen eintragen

### ...weitere Kategorien dazu sollen (Sanitaer, Elektro, Einbauten)

In beiden script.py-Dateien unter `KATEGORIEN` bzw. `ZIEL_KATEGORIEN` die
auskommentierten BuiltInCategory-Zeilen einblenden.

## Technische Hinweise

- Engine: CPython (pyRevit `#! python3`)
- Toleranz fuer Moebel knapp ausserhalb Raum: 50 mm in 8 Richtungen
  (anpassbar ueber `TOLERANZ_MM` in RaumAusLink/script.py)
- UI-Dialoge via `Autodesk.Revit.UI.TaskDialog`
  (`pyrevit.forms` ist unter CPython nicht unterstuetzt)
