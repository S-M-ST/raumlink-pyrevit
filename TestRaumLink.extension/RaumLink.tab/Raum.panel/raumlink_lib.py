"""RaumLink shared lib: Kategorie-Katalog, Auswahl-Dialog, Persistenz.

Liegt im Panel-Ordner, wird von beiden Pushbuttons (SharedParams,
RaumAusLink) ueber sys.path-Injection importiert.

Keine pyrevit-Abhaengigkeit - reines WinForms damit es auf IronPython +
CPython unter pyRevit 4.8 und 5.x gleichermassen laeuft.
"""
import os
import json

import clr
clr.AddReference("RevitAPI")
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from Autodesk.Revit.DB import BuiltInCategory
import System.Windows.Forms as WF


# Katalog: (Anzeige-Name, BuiltInCategory-Enum-Name).
# Nur Anzeige-Name verwenden wenn Enum in der Revit-Version existiert.
# Reihenfolge = Anzeige-Reihenfolge im Dialog.
_KATALOG_RAW = [
    ("Moebel",                   "OST_Furniture"),
    ("Moebelsysteme",            "OST_FurnitureSystems"),
    ("Einbauten (Casework)",     "OST_Casework"),
    ("Sanitaerinstallationen",   "OST_PlumbingFixtures"),
    ("Sanitaerausstattung",      "OST_PlumbingEquipment"),
    ("Elektroinstallationen",    "OST_ElectricalFixtures"),
    ("Elektroausstattung",       "OST_ElectricalEquipment"),
    ("Mechanische Ausstattung",  "OST_MechanicalEquipment"),
    ("Spezialausstattung",       "OST_SpecialityEquipment"),
    ("Beleuchtungskoerper",      "OST_LightingFixtures"),
    ("Allgemeines Modell",       "OST_GenericModel"),
]


def _baue_katalog():
    out = []
    for name, bic_name in _KATALOG_RAW:
        bic = getattr(BuiltInCategory, bic_name, None)
        if bic is not None:
            out.append((name, bic))
    return out


ALLE_KATEGORIEN = _baue_katalog()
DEFAULT_AUSWAHL = ["Moebel", "Moebelsysteme"]


def _config_path():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "user_categories.json")


def lade_auswahl():
    path = _config_path()
    if not os.path.isfile(path):
        return list(DEFAULT_AUSWAHL)
    try:
        with open(path, "r") as f:
            data = json.load(f)
        sel = data.get("selected", [])
        if not isinstance(sel, list):
            return list(DEFAULT_AUSWAHL)
        bekannt = set(n for n, _ in ALLE_KATEGORIEN)
        gefiltert = [s for s in sel if s in bekannt]
        return gefiltert or list(DEFAULT_AUSWAHL)
    except Exception:
        return list(DEFAULT_AUSWAHL)


def speichere_auswahl(namen):
    path = _config_path()
    try:
        with open(path, "w") as f:
            json.dump({"selected": list(namen)}, f, indent=2)
    except Exception:
        pass


def zeige_kategorie_dialog(titel="RaumLink - Kategorien waehlen"):
    """Zeigt CheckedListBox-Dialog, liefert Liste Anzeige-Namen.

    Returns None bei Abbruch oder leerer Auswahl.
    Speichert die Auswahl persistent fuer den naechsten Aufruf.
    """
    vor_ausgewaehlt = set(lade_auswahl())

    form = WF.Form()
    form.Text = titel
    form.Width = 380
    form.Height = 480
    form.StartPosition = WF.FormStartPosition.CenterScreen
    form.FormBorderStyle = WF.FormBorderStyle.FixedDialog
    form.MaximizeBox = False
    form.MinimizeBox = False

    label = WF.Label()
    label.Text = "Kategorien die gebunden / geschrieben werden sollen:"
    label.Left = 12
    label.Top = 12
    label.Width = 340
    form.Controls.Add(label)

    clb = WF.CheckedListBox()
    clb.Left = 12
    clb.Top = 38
    clb.Width = 340
    clb.Height = 320
    clb.CheckOnClick = True
    for name, _ in ALLE_KATEGORIEN:
        clb.Items.Add(name, name in vor_ausgewaehlt)
    form.Controls.Add(clb)

    btn_ok = WF.Button()
    btn_ok.Text = "OK"
    btn_ok.Left = 185
    btn_ok.Top = 370
    btn_ok.Width = 75
    btn_ok.DialogResult = WF.DialogResult.OK
    form.Controls.Add(btn_ok)
    form.AcceptButton = btn_ok

    btn_cancel = WF.Button()
    btn_cancel.Text = "Abbrechen"
    btn_cancel.Left = 270
    btn_cancel.Top = 370
    btn_cancel.Width = 80
    btn_cancel.DialogResult = WF.DialogResult.Cancel
    form.Controls.Add(btn_cancel)
    form.CancelButton = btn_cancel

    result = form.ShowDialog()
    if result != WF.DialogResult.OK:
        return None

    gewaehlt = [clb.Items[i] for i in range(clb.Items.Count)
                if clb.GetItemChecked(i)]
    if not gewaehlt:
        return None
    speichere_auswahl(gewaehlt)
    return gewaehlt


def namen_zu_bics(namen):
    lookup = dict(ALLE_KATEGORIEN)
    return [lookup[n] for n in namen if n in lookup]
