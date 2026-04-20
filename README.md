# RaumLink — pyRevit Panel

Schreibt Raumname + Raumnummer aus verknuepften Architekturmodellen in
Shared-Parameter an Moebel-Elementen im Host. Nachbau der Kernfunktion
von [RV RoomLink](https://rv-boost.com/rv-room-link/) als pyRevit-Panel
fuer den b.i.m.m-Kontext.

## Inhalt

```
TestRaumLink.extension/
├── INSTALL.md                       Detaillierte Installationsanleitung
├── RaumLink_SharedParams.txt        Mini-SharedParameters-Datei (2 Params)
└── RaumLink.tab/
    └── Raum.panel/
        ├── SharedParams.pushbutton/ [Setup, einmalig pro Projekt]
        └── RaumAusLink.pushbutton/  [Tool, so oft wie gebraucht]

HANDOFF_FUER_TS_SESSION.md           Kontext fuer TS-Claude-Code-Session
```

## Drop-in in bestehende Extension

Der Panel-Ordner `RaumLink.panel/` laesst sich in jede bestehende pyRevit
`.extension` einbauen — einfach in einen `.tab`-Ordner verschieben. Die
zentrale `RaumLink_SharedParams.txt` muss im Extension-Root liegen
(neben den .tab-Ordnern).

Details siehe `TestRaumLink.extension/INSTALL.md`.

## Engine

Scripts haben **keinen Shebang** → laufen auf pyRevit-Default-Engine
(auf pyRevit 5.x: IronPython 2.7.12). Zusaetzlich ist der
`from pyrevit import script` in try/except gewrappt — bei einem
CPython-Crash (z.B. `collections.Callable`-Bug in pyRevit 5 WIP) fallen
die Scripts auf reine TaskDialog + Temp-Datei-Reports zurueck.

## Parameter (b.i.m.m-Konvention)

| Name | GUID | Typ |
|---|---|---|
| `117_100_111_Raumname_Link` | `57acd0bc-8de7-409a-a920-3ab3efe061ba` | TEXT |
| `117_100_112_Raumnr_Link` | `49f093fd-9897-4a13-b51b-caf83120178e` | TEXT |

Gebunden als Instance-Parameter, Gruppe Identitaetsdaten, an
`OST_Furniture` + `OST_FurnitureSystems`.

## Fuer Claude-Code-Sessions

Siehe `HANDOFF_FUER_TS_SESSION.md` — enthaelt vollen Kontext fuer
Folge-Sessions auf dem Terminalserver (Environment, bekannte Quirks,
naechste Schritte).
