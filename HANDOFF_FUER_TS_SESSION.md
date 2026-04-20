# RaumLink – Handoff an Claude Code auf dem Terminalserver

> **So benutzen:** In die neue Claude-Code-Session auf dem TS einfach
> den Inhalt dieser Datei als erste Nachricht reinkopieren (oder die Datei
> ins Arbeitsverzeichnis legen und `cat HANDOFF_FUER_TS_SESSION.md` sagen).

---

## Worum es geht

Wir bauen ein **pyRevit-Panel `RaumLink`**, das Raum-Info (Name + Nummer)
aus verknuepften Architektur-Modellen in Moebel-Elemente im Host schreibt.
Ersatz / Eigenbau fuer das kommerzielle Plugin **RV RoomLink** von RV Boost.

**Ziel auf dem TS:** Das fertige Panel in eine bestehende BD-Extension
einbauen und dort verwenden.

## Was schon fertig ist

**Deployment-Pakete im Ordner `C:\Users\SebastianStrober\Desktop\Test Raum Link\`:**

- `RaumLink_panel_dropin.zip` — **das** zu installierende Paket
  (enthaelt `RaumLink.panel/` + `RaumLink_SharedParams.txt` + INSTALL.md + README)
- `TestRaumLink.extension.zip` — Backup, falls Standalone-Extension erwuenscht
- `ARCH.rvt` + `Moebel.rvt` — Testmodelle (3 Raeume, 3 Moebel)
- `0030_100_000_bimm_BD_GGP.txt` — Testkopie der zentralen b.i.m.m-GGP
  (mit lokal eingefuegten Raum_Link-Params; `.backup` daneben)

**Die Extension enthaelt:**
- Panel `RaumLink` mit 2 Pushbuttons:
  - `SharedParams binden` (blau, Icon "SP") — bindet die 2 Shared-Params
    an Moebel + Moebelsysteme (einmalig pro Projekt)
  - `Raum aus Link` (orange, Icon "R") — schreibt Raum-Name + -Nummer
    aus Link in die Moebel-Shared-Params
- Mitgelieferte Mini-SP-Datei `RaumLink_SharedParams.txt` mit den 2 Params:
  - `117_100_111_Raumname_Link` (GUID `57acd0bc-8de7-409a-a920-3ab3efe061ba`)
  - `117_100_112_Raumnr_Link` (GUID `49f093fd-9897-4a13-b51b-caf83120178e`)

## Technische Eckdaten

### Engine-Wahl (WICHTIG)

- **Scripts haben KEINEN Shebang** → pyRevit nimmt die Default-Engine.
- Auf pyRevit 5.0.1 WIP ist Default **IronPython 2.7.12**.
- Das umgeht den `collections.Callable`-Bug, den der WIP-Build auf CPython 3.12 hat
  (in `pyrevit/coreutils/pyutils.py` Zeile 13: `from collections import OrderedDict, Callable`
  — Callable ist seit Python 3.10 nach `collections.abc` gewandert).
- Als zusaetzliches Sicherheitsnetz haben die Scripts einen
  **try/except um den pyRevit-Import**: faellt auf reinen `TaskDialog` +
  Temp-Datei-Report zurueck, wenn `from pyrevit import script` crasht.

### Pfad-Konventionen

- Setup-Script sucht die SP-Datei unter `../../../RaumLink_SharedParams.txt`
  → das ist der Extension-Root (3 Ebenen ueber dem Pushbutton).
- Dort muss `RaumLink_SharedParams.txt` also direkt unter
  `<eure>.extension/` liegen — als Geschwister zu den .tab-Ordnern.

### UI-Ausgabe

- Bevorzugt `pyrevit.script` Output-Fenster (Markdown-Tabelle).
- Fallback: `TaskDialog.Show` + Temp-.txt-Report, der mit `webbrowser.open`
  angestossen wird.

### Fehlerbehandlung

- `lese_raum_info()` nutzt mehrstufige Kaskade:
  1. `LookupParameter("Name")` (dt. Revit zeigt ROOM_NAME als "Name")
  2. Parameter-Iteration mit `Definition.Name == "Name"`
  3. Fallback: `raum.Name` minus " Nummer"-Suffix
  - Grund: `raum.get_Parameter(BuiltInParameter.ROOM_NAME)` hat auf
    CPython/PythonNet einen Overload-Resolution-Bug; `raum.Name` liefert
    "Name + Nummer" konkateniert und kann auf linked Rooms leer sein.
- Pro Element try/except im Transaction-Loop → einzelne Fehler bremsen
  den Rest nicht aus.

## Was als naechstes zu tun ist auf dem TS

### 1. BD-Extension finden

Suche im TS nach dem Ordner mit dem Unternehmens-Extension. Kandidaten:

```powershell
Get-ChildItem -Path "C:\ProgramData\pyRevit*", `
  "$env:APPDATA\pyRevit*", `
  "C:\pyRevit-*", `
  "$env:APPDATA\Autodesk\Revit\Addins" `
  -Directory -Recurse -Filter "*.extension" -ErrorAction SilentlyContinue | `
  Select FullName
```

Oder im pyRevit selbst: *pyRevit-Tab → Settings → Custom Extension Directories*.

### 2. Panel-Drop-in einbauen

ZIP entpacken und:
- `RaumLink.panel/` → in einen Tab (z.B. `BD.tab/`) innerhalb der BD-Extension
- `RaumLink_SharedParams.txt` → direkt in den Extension-Root (neben den .tab-Ordnern)

### 3. pyRevit neu laden

pyRevit-Tab → Reload. Neuer Panel-Titel "RaumLink" sollte im gewaehlten Tab
erscheinen, mit 2 Buttons + Icons.

### 4. In einem Projekt testen

1. Revit-Projekt oeffnen mit:
   - Einer verknuepften ARCH.rvt mit Raeumen
   - Moebeln im Host-Modell mit aktiviertem Raumberechnungspunkt
2. Neu-Panel **RaumLink** → **SharedParams binden** (einmalig)
   - Erwartet: Report "2 importiert, 0 aktualisiert, 0 Fehler"
3. **Raum aus Link**
   - Erwartet: Tabelle "Elemente gesamt / Raum zugeordnet / ..."
   - Pro Moebel werden `117_100_111_Raumname_Link` und `117_100_112_Raumnr_Link`
     gefuellt

### 5. Wenn Fehler: Engine pruefen

Falls der Button crasht oder nichts passiert:

- `pyRevit-Tab → About` → welche Engine wird angezeigt?
  Erwartet: "Running on IronPython 2.7.12".
- Wenn CPython 3.12 dort steht: Bundle-Engine-Override setzen, in jeder
  `pushbutton/bundle.yaml`:
  ```yaml
  engine_mgr:
    type: ipy
  ```
- Alternative: Admin patcht `C:\Program Files\pyRevit-Master1\pyrevitlib\pyrevit\coreutils\pyutils.py`
  Zeile 13:
  ```python
  # from collections import OrderedDict, Callable
  from collections import OrderedDict
  from collections.abc import Callable
  ```

## Environment auf dem TS (Stand 2026-04-20)

- Windows, b.i.m.m Terminalserver (AGA-BAU-Domain)
- User: `AGA-BAU.COM\BuD_StSe`
- Revit 2024.2 (vermutlich, ggf. pruefen)
- pyRevit 5.0.1.25064+1410-wip
- Engines: IronPython 2.7.12 (Default) + CPython 3.12.3
- Rocket-mode aktiv

## Was der User (Sebastian Strober) ist

- BIM-Manager, keine Programmierkenntnisse, nutzt Claude Code als Umsetzer
- Deutsche Sprache, deutsche Revit-Installation
- Praeferiert pragmatische Loesungen ueber elegante Architektur
- Auto-Mode ist meist aktiv — direkt umsetzen, nicht fragen

## Relevante Referenzen (nicht auf TS, nur als Hintergrund)

- Lokale Entwicklungskopie: `D:\OneDrive - Strober-Planung\11_Claude\FuralPlugIn\roomlink\`
- RV RoomLink (Vorbild): https://rv-boost.com/rv-room-link/
- pyRevit Bug (collections.Callable): siehe Stack-Trace unten

## Original-Stacktrace des Bugs (falls wieder auftritt)

```
CPython Traceback:
cannot import name 'Callable' from 'collections' (C:\Program Files\pyRevit-Master1\bin\cengines\CPY3123\python312.zip\collections\__init__.pyc)

File "C:\Program Files\pyRevit-Master1\pyrevitlib\pyrevit\coreutils\pyutils.py", line 13, in <module>
  from collections import OrderedDict, Callable #pylint: disable=E0611
File "C:\Program Files\pyRevit-Master1\pyrevitlib\pyrevit\extensions\genericcomps.py", line 12, in <module>
  from pyrevit.coreutils import pyutils
File "C:\Program Files\pyRevit-Master1\pyrevitlib\pyrevit\script.py", line 36, in <module>
  from pyrevit.extensions.genericcomps import GenericUICommand
File "<string>", line 23, in <module>
```

---

## Erste Claude-Code-Nachricht auf dem TS (Vorschlag zum Copy&Paste)

> Hallo Claude. Ich arbeite am Terminalserver an der Integration einer
> pyRevit-Extension namens "RaumLink". Der vollstaendige Kontext steht in
> `HANDOFF_FUER_TS_SESSION.md` — bitte lies die Datei und lege dann los
> mit Punkt 1 (BD-Extension finden) und danach Panel einbauen + testen.
> Es ist Auto-Mode, kein grosses Nachfragen bitte, einfach umsetzen.
