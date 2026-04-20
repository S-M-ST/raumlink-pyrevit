"""
RaumAusLink - Moebel -> Raum aus verknuepftem Modell

Kein Shebang: laeuft auf pyRevit-Default-Engine.
Auf pyRevit 4.8 (CPY385) und 5.x (IronPython-Default) unterstuetzt.

Liest Raumname + Raumnummer aus allen verknuepften Architektur-Modellen
und schreibt sie in Shared Parameter an den Moebel-Elementen im Host.

Voraussetzung (einmalig pro Projekt):
    Button 'SharedParams binden' im gleichen Panel klicken -
    bindet die Params 117_100_111_Raumname_Link und
    117_100_112_Raumnr_Link an Moebel + Moebelsysteme.
"""

import os
import tempfile
import webbrowser

import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
from Autodesk.Revit.DB import (
    BuiltInCategory,
    BuiltInParameter,
    FilteredElementCollector,
    LocationPoint,
    RevitLinkInstance,
    StorageType,
    Transaction,
    XYZ,
)
from Autodesk.Revit.UI import TaskDialog

# pyrevit.script ist auf pyRevit 5.0.1 WIP mit Python 3.12 kaputt
# (from collections import Callable). Abgesichert importieren.
_report_lines = []
try:
    from pyrevit import script as _pyscript
    _pyrv_out = _pyscript.get_output()
    _HAS_PYREVIT = True
except Exception:
    _pyrv_out = None
    _HAS_PYREVIT = False


def log(md):
    """Zeile in Report aufnehmen; falls pyRevit verfuegbar auch live anzeigen."""
    _report_lines.append(md)
    if _HAS_PYREVIT:
        try:
            _pyrv_out.print_md(md)
        except Exception:
            pass


def linkify_id(el_id):
    """Klickbarer Link wenn pyRevit-Output da, sonst reiner Text."""
    if _HAS_PYREVIT:
        try:
            return _pyrv_out.linkify(el_id)
        except Exception:
            pass
    try:
        return "Id {}".format(el_id.IntegerValue)
    except Exception:
        return "Id {}".format(el_id)


def finalize_report():
    """Wenn pyRevit kein Output-Fenster lieferte, Report als Datei oeffnen."""
    if _HAS_PYREVIT:
        return
    # Einfache Markdown -> Plaintext-Umsetzung
    def strip_md(s):
        return (s.replace("**", "")
                 .replace("`", "")
                 .replace("# ", "")
                 .replace("## ", "")
                 .replace("|", " "))
    fd, path = tempfile.mkstemp(suffix=".txt", prefix="raumlink_")
    os.close(fd)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(strip_md(l) for l in _report_lines))
    try:
        webbrowser.open(path)
    except Exception:
        pass


# ============ KONFIG ============

KATEGORIEN = [
    BuiltInCategory.OST_Furniture,
    BuiltInCategory.OST_FurnitureSystems,
    # bei Bedarf erweitern:
    # BuiltInCategory.OST_PlumbingFixtures,
    # BuiltInCategory.OST_ElectricalFixtures,
    # BuiltInCategory.OST_ElectricalEquipment,
    # BuiltInCategory.OST_Casework,
    # BuiltInCategory.OST_SpecialityEquipment,
]

PARAM_RAUM_NAME = "117_100_111_Raumname_Link"
PARAM_RAUM_NUMMER = "117_100_112_Raumnr_Link"

TOLERANZ_MM = 50.0

# ================================


MM_TO_FEET = 1.0 / 304.8
doc = __revit__.ActiveUIDocument.Document  # noqa: F821


def abbruch(message):
    TaskDialog.Show("RaumLink", message)
    raise SystemExit


def sammle_raeume_aus_links():
    ergebnis = []
    link_col = FilteredElementCollector(doc).OfClass(RevitLinkInstance)
    for link in link_col:
        link_doc = link.GetLinkDocument()
        if link_doc is None:
            continue
        transform = link.GetTotalTransform()
        raum_col = (
            FilteredElementCollector(link_doc)
            .OfCategory(BuiltInCategory.OST_Rooms)
            .WhereElementIsNotElementType()
        )
        for raum in raum_col:
            try:
                if raum.Area > 0:
                    ergebnis.append((raum, transform, link_doc.Title))
            except Exception:
                continue
    return ergebnis


def hole_pruefpunkt(elem):
    try:
        if getattr(elem, "HasSpatialElementCalculationPoint", False):
            pt = elem.GetSpatialElementCalculationPoint()
            if pt is not None:
                return pt
    except Exception:
        pass
    loc = getattr(elem, "Location", None)
    if isinstance(loc, LocationPoint):
        return loc.Point
    return None


def finde_raum(punkt, raeume, toleranz_feet):
    def check(p):
        for raum, transform, _ in raeume:
            lokaler_punkt = transform.Inverse.OfPoint(p)
            try:
                if raum.IsPointInRoom(lokaler_punkt):
                    return raum
            except Exception:
                continue
        return None

    treffer = check(punkt)
    if treffer is not None:
        return treffer

    if toleranz_feet <= 0:
        return None

    offsets = [
        XYZ(toleranz_feet, 0, 0),
        XYZ(-toleranz_feet, 0, 0),
        XYZ(0, toleranz_feet, 0),
        XYZ(0, -toleranz_feet, 0),
        XYZ(toleranz_feet, toleranz_feet, 0),
        XYZ(-toleranz_feet, toleranz_feet, 0),
        XYZ(toleranz_feet, -toleranz_feet, 0),
        XYZ(-toleranz_feet, -toleranz_feet, 0),
    ]
    for offset in offsets:
        treffer = check(punkt + offset)
        if treffer is not None:
            return treffer
    return None


def setze_text_param(elem, param_name, wert):
    p = elem.LookupParameter(param_name)
    if p is None:
        return False, "Parameter '{}' fehlt".format(param_name)
    if p.IsReadOnly:
        return False, "Parameter '{}' ist ReadOnly".format(param_name)
    if p.StorageType != StorageType.String:
        return False, "Parameter '{}' ist kein Text".format(param_name)
    p.Set(wert if wert is not None else "")
    return True, None


def lese_raum_info(raum):
    """Liefert (Name, Nummer) - mehrstufige Fallback-Kaskade gegen PythonNet-Quirks.

    - Nummer: typed Property Room.Number (funktioniert).
    - Name: LookupParameter("Name") -> Definition-Name-Iteration ->
      raum.Name minus Nummer-Suffix.
      Grund: Room.Name liefert Name + " " + Nummer konkateniert und ist
      auf CPython/Linked-Docs unzuverlaessig; get_Parameter(BIP) hat
      einen PythonNet-Overload-Resolution-Bug.
    """
    name = ""
    num = ""

    try:
        if raum.Number:
            num = str(raum.Number)
    except Exception:
        pass

    # Strategie 1: LookupParameter mit der in dt. Revit sichtbaren
    # Anzeige-Bezeichnung "Name" des ROOM_NAME-BuiltInParameter
    try:
        p = raum.LookupParameter("Name")
        if p is not None and p.StorageType == StorageType.String:
            val = p.AsString()
            if val:
                name = str(val)
    except Exception:
        pass

    # Strategie 2: Parameter-Iteration auf Definition.Name == "Name"
    if not name:
        try:
            for p in raum.Parameters:
                try:
                    if p.StorageType != StorageType.String:
                        continue
                    dname = p.Definition.Name
                    if dname == "Name":
                        val = p.AsString()
                        if val:
                            name = str(val)
                            break
                except Exception:
                    continue
        except Exception:
            pass

    # Strategie 3: Fallback ueber raum.Name minus " Nummer"-Suffix
    if not name:
        try:
            raw = raum.Name or ""
            if raw:
                if num and raw.endswith(" " + num):
                    name = raw[:-(len(num) + 1)]
                else:
                    name = raw
        except Exception:
            pass

    return name, num


def sammle_elemente():
    elemente = []
    for cat in KATEGORIEN:
        col = (
            FilteredElementCollector(doc)
            .OfCategory(cat)
            .WhereElementIsNotElementType()
        )
        elemente.extend(col.ToElements())
    return elemente


def pruefe_parameter_vorhanden(elemente):
    if not elemente:
        return True, []
    sample = elemente[0]
    fehlen = []
    for pname in (PARAM_RAUM_NAME, PARAM_RAUM_NUMMER):
        if sample.LookupParameter(pname) is None:
            fehlen.append(pname)
    return len(fehlen) == 0, fehlen


def stelle_vary_across_groups_sicher(param_namen):
    # Setzt "Werte koennen pro Gruppeninstanz variieren" auf den bound
    # InternalDefinitions. Ohne das wirft Revit beim Schreiben innerhalb
    # einer Modellgruppe: "Aenderungen an Gruppen sind nur im
    # Gruppenbearbeitungsmodus zulaessig."
    geaendert = []
    binding_map = doc.ParameterBindings
    t = Transaction(doc, "RaumLink: VaryAcrossGroups setzen")
    t.Start()
    try:
        it = binding_map.ForwardIterator()
        it.Reset()
        while it.MoveNext():
            d = it.Key
            if d is None or d.Name not in param_namen:
                continue
            try:
                if not d.VariesAcrossGroups:
                    d.SetAllowVaryBetweenGroups(doc, True)
                    geaendert.append(d.Name)
            except Exception:
                pass
        t.Commit()
    except Exception:
        try:
            t.RollBack()
        except Exception:
            pass
    return geaendert


def main():
    raeume = sammle_raeume_aus_links()
    if not raeume:
        abbruch(
            "Keine Raeume in verknuepften Modellen gefunden.\n\n"
            "Pruefe: Architektur-Link geladen? Raeume im Link platziert?"
        )

    elemente = sammle_elemente()
    if not elemente:
        abbruch("Keine Elemente der konfigurierten Kategorien im Modell gefunden.")

    ok, fehlende = pruefe_parameter_vorhanden(elemente)
    if not ok:
        abbruch(
            "Shared Parameter fehlen an den Moebel-Kategorien:\n\n"
            "  - {}\n\n"
            "Klick zuerst den Button 'SharedParams binden' im gleichen Panel - "
            "der bindet die b.i.m.m-Params aus der GGP-Datei automatisch.".format(
                "\n  - ".join(fehlende)
            )
        )

    nachgezogen = stelle_vary_across_groups_sicher(
        (PARAM_RAUM_NAME, PARAM_RAUM_NUMMER)
    )
    if nachgezogen:
        log("- VaryAcrossGroups nachgezogen fuer: {}".format(", ".join(nachgezogen)))

    toleranz_feet = TOLERANZ_MM * MM_TO_FEET

    gefunden = 0
    ohne_raum = []
    ohne_punkt = []
    schreibfehler = []

    import traceback

    t = Transaction(doc, "Raum-Info aus Link schreiben")
    t.Start()
    try:
        for elem in elemente:
            try:
                punkt = hole_pruefpunkt(elem)
                if punkt is None:
                    ohne_punkt.append(elem)
                    continue

                raum = finde_raum(punkt, raeume, toleranz_feet)
                if raum is None:
                    ohne_raum.append(elem)
                    continue

                raum_name, raum_num = lese_raum_info(raum)

                ok1, err1 = setze_text_param(elem, PARAM_RAUM_NAME, raum_name)
                ok2, err2 = setze_text_param(elem, PARAM_RAUM_NUMMER, raum_num)

                if ok1 and ok2:
                    gefunden += 1
                else:
                    schreibfehler.append((elem, err1 or err2))
            except Exception as elem_ex:
                schreibfehler.append(
                    (elem, "Ausnahme: {} ({})".format(elem_ex, type(elem_ex).__name__))
                )

        t.Commit()
    except Exception as ex:
        try:
            t.RollBack()
        except Exception:
            pass
        tb = traceback.format_exc()
        log("## Abbruch - Transaktion fehlgeschlagen")
        log("**Typ:** `{}`".format(type(ex).__name__))
        log("**Fehler:** {}".format(ex))
        log("```\n{}\n```".format(tb))
        abbruch(
            "Transaktion fehlgeschlagen:\n{}: {}\n\n"
            "Details im pyRevit-Ausgabefenster.".format(type(ex).__name__, ex)
        )

    log("# Raum-Link Ergebnis")
    log("| | |")
    log("|---|---:|")
    log("| Elemente gesamt | {} |".format(len(elemente)))
    log("| Raum zugeordnet | **{}** |".format(gefunden))
    log("| Ohne Raumtreffer | {} |".format(len(ohne_raum)))
    log("| Ohne Einfuegepunkt | {} |".format(len(ohne_punkt)))
    log("| Schreibfehler | {} |".format(len(schreibfehler)))
    log("| Raeume in Links | {} |".format(len(raeume)))

    if ohne_raum:
        log("## Elemente ohne Raumtreffer (erste 25)")
        log(
            "Pruefe: Raumberechnungspunkt aktiv? Element im richtigen Stockwerk? "
            "Toleranz zu klein? ({} mm)".format(int(TOLERANZ_MM))
        )
        for elem in ohne_raum[:25]:
            link_txt = linkify_id(elem.Id)
            try:
                name = elem.Name or "(ohne Name)"
            except Exception:
                name = "(ohne Name)"
            log("- {} - {}".format(link_txt, name))
        if len(ohne_raum) > 25:
            log("_...und {} weitere_".format(len(ohne_raum) - 25))

    if ohne_punkt:
        log("## Elemente ohne Einfuegepunkt")
        for elem in ohne_punkt[:10]:
            log("- {}".format(linkify_id(elem.Id)))

    if schreibfehler:
        log("## Schreibfehler")
        for elem, err in schreibfehler[:10]:
            log("- {} - {}".format(linkify_id(elem.Id), err))

    finalize_report()


if __name__ == "__main__":
    main()
