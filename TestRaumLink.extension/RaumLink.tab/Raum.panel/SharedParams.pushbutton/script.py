"""SharedParams binden - Raumname_Link + Raumnr_Link an Moebel.

Kein Shebang: laeuft auf pyRevit-Default-Engine (auf v5 IronPython 2.7).

Liest die b.i.m.m-GGP-Datei (eine Ebene ueber der Extension) und bindet
die beiden Ziel-Shared-Parameter an OST_Furniture + OST_FurnitureSystems
als Instance-Parameter in der Gruppe "Identitaetsdaten".

Muster-Nachbau von Fural.extension/.../SharedParams.pushbutton.
"""
import os
import tempfile
import webbrowser

import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
from Autodesk.Revit.DB import (
    BuiltInCategory,
    CategorySet,
    GroupTypeId,
    InstanceBinding,
    Transaction,
)
from Autodesk.Revit.UI import TaskDialog


doc = __revit__.ActiveUIDocument.Document  # noqa: F821
app = doc.Application

# pyrevit.script ist auf pyRevit 5.0.1 WIP (Python 3.12) kaputt.
# Fallback auf reine TaskDialog / File-Ausgabe.
_report_lines = []
try:
    from pyrevit import script as _pyscript
    _pyrv_out = _pyscript.get_output()
    _HAS_PYREVIT = True
except Exception:
    _pyrv_out = None
    _HAS_PYREVIT = False


def log(md):
    _report_lines.append(md)
    if _HAS_PYREVIT:
        try:
            _pyrv_out.print_md(md)
        except Exception:
            pass


def finalize_report():
    if _HAS_PYREVIT:
        return
    def strip_md(s):
        return (s.replace("**", "")
                 .replace("`", "")
                 .replace("# ", "")
                 .replace("## ", ""))
    fd, path = tempfile.mkstemp(suffix=".txt", prefix="raumlink_setup_")
    os.close(fd)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(strip_md(l) for l in _report_lines))
    try:
        webbrowser.open(path)
    except Exception:
        pass


# ============ KONFIG ============

# Eigene Mini-SharedParameters-Datei. Sucht bottom-up vom pushbutton hoch,
# damit Installation in beliebige Ebene (pushbutton, panel, tab, extension)
# funktioniert. Erste gefundene Datei gewinnt.
_HERE = os.path.dirname(os.path.abspath(__file__))
_PARAM_FILE_NAME = "RaumLink_SharedParams.txt"


def _find_param_file(start_dir, filename, max_up=6):
    cur = start_dir
    for _ in range(max_up + 1):
        candidate = os.path.join(cur, filename)
        if os.path.isfile(candidate):
            return os.path.normpath(candidate)
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return None


_PARAM_FILE = _find_param_file(_HERE, _PARAM_FILE_NAME)

# Zu bindende Parameter aus der GGP
ZIEL_PARAMS = [
    "117_100_111_Raumname_Link",
    "117_100_112_Raumnr_Link",
]

# Zielkategorien
ZIEL_KATEGORIEN = [
    BuiltInCategory.OST_Furniture,
    BuiltInCategory.OST_FurnitureSystems,
]

# ================================


def abbruch(titel, message):
    TaskDialog.Show(titel, message)
    raise SystemExit


log("# SharedParams binden - Raum an Moebel")

if _PARAM_FILE is None or not os.path.isfile(_PARAM_FILE):
    abbruch(
        "RaumLink Setup",
        "SharedParameters-Datei '{}' nicht gefunden.\n\n"
        "Gesucht wurde von:\n  {}\n"
        "bis zur Laufwerkswurzel.\n\n"
        "Datei in einen dieser Ordner legen "
        "(pushbutton, panel, tab oder extension).".format(
            _PARAM_FILE_NAME, _HERE),
    )

# Aktuelle SharedParametersFile merken + temporaer umbiegen
_orig_file = app.SharedParametersFilename
try:
    app.SharedParametersFilename = _PARAM_FILE
except Exception as ex:
    abbruch("RaumLink Setup", "SharedParametersFilename nicht setzbar:\n{}".format(ex))

sp_file = app.OpenSharedParameterFile()
if sp_file is None:
    try:
        app.SharedParametersFilename = _orig_file
    except Exception:
        pass
    abbruch(
        "RaumLink Setup",
        "SharedParameters-Datei konnte nicht geoeffnet werden:\n\n{}".format(_PARAM_FILE),
    )

# Definitionen suchen
gesucht = {}
for pname in ZIEL_PARAMS:
    gesucht[pname] = None
for group in sp_file.Groups:
    for defn in group.Definitions:
        if defn.Name in gesucht:
            gesucht[defn.Name] = defn

fehlt = []
for pname, defn in gesucht.items():
    if defn is None:
        fehlt.append(pname)

if fehlt:
    try:
        app.SharedParametersFilename = _orig_file
    except Exception:
        pass
    abbruch(
        "RaumLink Setup",
        "Diese Parameter fehlen in der SharedParameters-Datei:\n\n  - {}".format(
            "\n  - ".join(fehlt)
        ),
    )

# Kategorie-Set aufbauen via Iteration (PythonNet-sicher)
ziel_ints = set()
for bic in ZIEL_KATEGORIEN:
    ziel_ints.add(int(bic))

cat_set = CategorySet()
gefunden_namen = []
for cat in doc.Settings.Categories:
    try:
        iv = cat.Id.IntegerValue
    except Exception:
        continue
    if iv in ziel_ints:
        cat_set.Insert(cat)
        gefunden_namen.append(cat.Name)

if cat_set.IsEmpty:
    try:
        app.SharedParametersFilename = _orig_file
    except Exception:
        pass
    abbruch(
        "RaumLink Setup",
        "Zielkategorien im Projekt nicht gefunden.\n\n"
        "Erwartet: Moebel, Moebelsysteme.",
    )

for kn in gefunden_namen:
    log("- Kategorie gefunden: **{}**".format(kn))

binding_map = doc.ParameterBindings

t = Transaction(doc, "RaumLink SharedParams binden")
t.Start()
try:
    importiert = 0
    aktualisiert = 0
    fehler = 0
    for pname in ZIEL_PARAMS:
        defn = gesucht[pname]
        bind = InstanceBinding(cat_set)
        try:
            if binding_map.Contains(defn):
                binding_map.ReInsert(defn, bind, GroupTypeId.IdentityData)
                aktualisiert += 1
                log("- `{}` **aktualisiert**".format(pname))
            else:
                binding_map.Insert(defn, bind, GroupTypeId.IdentityData)
                importiert += 1
                log("- `{}` **importiert**".format(pname))
        except Exception as ex:
            fehler += 1
            log("- `{}` **Fehler**: {}".format(pname, ex))
    t.Commit()
    log(
        "\n**Ergebnis:** {} importiert, {} aktualisiert, {} Fehler".format(
            importiert, aktualisiert, fehler
        )
    )
    log("- Quelle: `{}`".format(_PARAM_FILE))
except Exception as ex:
    t.RollBack()
    log("**FEHLER:** {}".format(ex))
finally:
    try:
        app.SharedParametersFilename = _orig_file
    except Exception:
        pass

log("**Fertig.** Jetzt den Button 'Raum aus Link' klicken.")

finalize_report()
