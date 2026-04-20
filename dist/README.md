# RaumLink drop-in ZIP

Fertig gepackter Panel-Ordner zum **direkt reinkopieren** in eine
bestehende pyRevit-Extension.

## Download

[RaumLink.panel.zip](https://github.com/S-M-ST/raumlink-pyrevit/raw/claude/fix-sharedparams-binding-kPDMV/dist/RaumLink.panel.zip)

## Installation

1. ZIP herunterladen und entpacken
2. Den Ordner `RaumLink.panel` komplett in die bestehende Tab-Ebene
   einer Extension kopieren, z.B.:

   ```
   Q:\...\pyBD.extension\pyBD.tab\RaumLink.panel\
   ```

3. In Revit: pyRevit -> Reload
4. Tab mit dem RaumLink-Panel oeffnen

## Inhalt

```
RaumLink.panel/
  bundle.yaml
  raumlink_lib.py              # shared Helper (Kategorie-Dialog + Persistenz)
  RaumLink_SharedParams.txt    # SharedParameters fuer 2 Ziel-Params
  SharedParams.pushbutton/
    bundle.yaml
    icon.png
    script.py
  RaumAusLink.pushbutton/
    bundle.yaml
    icon.png
    script.py
```

## Nach Update

Bei Neu-Download vom ZIP die vorhandene `RaumLink.panel` ueberschreiben
lassen. Die `user_categories.json` (Auswahl-Persistenz) ist NICHT im
ZIP - sie bleibt beim Update erhalten.
