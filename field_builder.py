from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsField, QgsProject, QgsMessageLog, Qgis


BASE_EXPR = {
    ("area",   "m2"):  "$area",
    ("area",   "km2"): "$area / 1000000",
    ("length", "m"):   "$length",
    ("length", "km"):  "$length / 1000",
    ("x",      None):  "$x",
    ("y",      None):  "$y",
}

NAME_PREFIX = {
    ("area",   "m2"):  "area_m2",
    ("area",   "km2"): "area_km2",
    ("length", "m"):   "length_m",
    ("length", "km"):  "length_km",
    ("x",      None):  "x_coord",
    ("y",      None):  "y_coord",
}


def _unique_name(layer, base):
    existing = {f.name() for f in layer.fields()}
    if base not in existing:
        return base
    i = 2
    while f"{base}_{i}" in existing:
        i += 1
    return f"{base}_{i}"


def _ensure_ellipsoid():
    proj = QgsProject.instance()
    if not proj.ellipsoid() or proj.ellipsoid().upper() in ("", "NONE"):
        proj.setEllipsoid("WGS84")


def add_virtual_field(layer, mode, unit=None, decimals=3):
    """Add a virtual field to the layer.

    mode: "area" | "length" | "x" | "y"
    unit: m2/km2 for area, m/km for length, ignored for x/y.
    Returns (True, field_name) or (False, error_message).
    """
    if mode in ("area", "length"):
        _ensure_ellipsoid()

    key = (mode, unit if mode in ("area", "length") else None)
    base_expr = BASE_EXPR.get(key)
    if base_expr is None:
        return False, f"Unknown mode/unit: {mode}/{unit}"

    try:
        decimals = int(decimals)
    except (TypeError, ValueError):
        decimals = 3
    decimals = max(0, min(decimals, 15))

    expression = f"round({base_expr}, {decimals})"
    name = _unique_name(layer, NAME_PREFIX[key])
    field = QgsField(name, QVariant.Double)

    try:
        idx = layer.addExpressionField(expression, field)
    except Exception as e:
        QgsMessageLog.logMessage(
            f"addExpressionField failed: {e}", "AreaLength", Qgis.Critical
        )
        return False, str(e)

    if idx < 0:
        return False, "QGIS refused to add the virtual field."

    return True, name
