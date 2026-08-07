from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsField, QgsProject, QgsMessageLog, Qgis


# Coordinate transform expressions.
_XY_PROJECT = {
    "x": "x(transform($geometry, layer_property(@layer, 'crs'), @project_crs))",
    "y": "y(transform($geometry, layer_property(@layer, 'crs'), @project_crs))",
}
_XY_WGS84 = {
    "x": "x(transform($geometry, layer_property(@layer, 'crs'), 'EPSG:4326'))",
    "y": "y(transform($geometry, layer_property(@layer, 'crs'), 'EPSG:4326'))",
}

BASE_EXPR = {
    ("area",   "m2"):      "$area",
    ("area",   "km2"):     "$area / 1000000",
    ("length", "m"):       "$length",
    ("length", "km"):      "$length / 1000",
    ("x",      "project"): _XY_PROJECT["x"],
    ("x",      "wgs84"):   _XY_WGS84["x"],
    ("y",      "project"): _XY_PROJECT["y"],
    ("y",      "wgs84"):   _XY_WGS84["y"],
}

NAME_PREFIX = {
    ("area",   "m2"):      "area_m2",
    ("area",   "km2"):     "area_km2",
    ("length", "m"):       "length_m",
    ("length", "km"):      "length_km",
    ("x",      "project"): "x_proj",
    ("x",      "wgs84"):   "longitude",
    ("y",      "project"): "y_proj",
    ("y",      "wgs84"):   "latitude",
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
    """Add a virtual field.

    mode: "area" | "length" | "x" | "y"
    unit: m2/km2 for area, m/km for length, project/wgs84 for x/y.
    """
    if mode in ("area", "length"):
        _ensure_ellipsoid()

    key = (mode, unit)
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
            f"addExpressionField failed: {e}", "AttributeTableFunctions", Qgis.Critical
        )
        return False, str(e)

    if idx < 0:
        return False, "QGIS refused to add the virtual field."

    return True, name
