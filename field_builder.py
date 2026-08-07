from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsField, QgsProject, QgsMessageLog, Qgis


AREA_EXPR = {
    "m2":  "$area",
    "km2": "$area / 1000000",
}
LENGTH_EXPR = {
    "m":  "$length",
    "km": "$length / 1000",
}
NAME_PREFIX = {
    "m2":  "area_m2",
    "km2": "area_km2",
    "m":   "length_m",
    "km":  "length_km",
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


def add_virtual_field(layer, mode, unit):
    """Add a virtual field to the layer computing area or length in the chosen unit.

    Returns (True, field_name) on success, (False, error_message) on failure.
    """
    _ensure_ellipsoid()

    if mode == "area":
        expression = AREA_EXPR.get(unit)
    elif mode == "length":
        expression = LENGTH_EXPR.get(unit)
    else:
        return False, f"Unknown mode: {mode}"

    if expression is None:
        return False, f"Unknown unit: {unit}"

    name = _unique_name(layer, NAME_PREFIX[unit])
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
