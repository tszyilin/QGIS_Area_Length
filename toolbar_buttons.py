from qgis.PyQt.QtWidgets import QToolBar, QMessageBox, QFileDialog
try:
    from qgis.PyQt.QtGui import QAction  # Qt6
except ImportError:
    from qgis.PyQt.QtWidgets import QAction  # Qt5
from qgis.PyQt.QtGui import QIcon
from qgis.core import (
    QgsWkbTypes, QgsMessageLog, Qgis, QgsProject,
    QgsVectorFileWriter, QgsCoordinateTransformContext,
)

from .unit_dialog import UnitDialog
from .field_builder import add_virtual_field


_INJECTED_ATTR = "_area_length_injected"


def _log(msg):
    QgsMessageLog.logMessage(str(msg), "AreaLength", Qgis.Info)


def _icon(name):
    import os
    path = os.path.join(os.path.dirname(__file__), "icons", name)
    if os.path.exists(path):
        return QIcon(path)
    return QIcon()


def _resolve_layer(dialog, iface):
    title = (dialog.windowTitle() or "")
    name = title
    for sep in (" — ", " – ", " - "):
        if sep in name:
            name = name.split(sep, 1)[0]
            break
    name = name.strip()
    if name:
        for layer in QgsProject.instance().mapLayers().values():
            if layer.name() == name and hasattr(layer, "geometryType"):
                return layer
    return iface.activeLayer() if iface is not None else None


_REQUIRED_GEOM = {
    "area":   (QgsWkbTypes.PolygonGeometry, "polygon"),
    "length": (QgsWkbTypes.LineGeometry, "line"),
    "x":      (QgsWkbTypes.PointGeometry, "point"),
    "y":      (QgsWkbTypes.PointGeometry, "point"),
}


def _on_click(dialog, iface, mode):
    layer = _resolve_layer(dialog, iface)
    if layer is None or not hasattr(layer, "geometryType"):
        QMessageBox.warning(dialog, "No layer",
                            "Could not determine the layer for this attribute table.")
        return
    required, label = _REQUIRED_GEOM[mode]
    if layer.geometryType() != required:
        QMessageBox.warning(dialog, "Wrong geometry",
                            f"'{mode.upper()}' requires a {label} layer. "
                            f"'{layer.name()}' is not a {label} layer.")
        return

    dlg = UnitDialog(mode, parent=dialog)
    if dlg.exec_() != dlg.Accepted:
        return
    unit = dlg.selected_unit()  # may be None for x/y
    decimals = dlg.decimals()
    ok, result = add_virtual_field(layer, mode, unit=unit, decimals=decimals)
    if ok:
        QMessageBox.information(
            dialog, "Field added",
            f"Virtual field '{result}' added to layer '{layer.name()}'."
        )
    else:
        QMessageBox.warning(dialog, "Failed",
                            f"Could not add virtual field:\n{result}")


def _on_export_csv(dialog, iface):
    layer = _resolve_layer(dialog, iface)
    if layer is None:
        QMessageBox.warning(dialog, "No layer",
                            "Could not determine the layer for this attribute table.")
        return

    default_name = f"{layer.name()}.csv"
    path, _ = QFileDialog.getSaveFileName(
        dialog, "Export attribute table to CSV", default_name, "CSV files (*.csv)"
    )
    if not path:
        return
    if not path.lower().endswith(".csv"):
        path += ".csv"

    only_selected = False
    if layer.selectedFeatureCount() > 0:
        reply = QMessageBox.question(
            dialog, "Export selection?",
            f"{layer.selectedFeatureCount()} feature(s) are selected. "
            "Export only the selection? (No = export all)",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes,
        )
        if reply == QMessageBox.Cancel:
            return
        only_selected = (reply == QMessageBox.Yes)

    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "CSV"
    options.fileEncoding = "UTF-8"
    options.onlySelectedFeatures = only_selected
    # Include geometry as WKT so users don't silently lose it.
    options.layerOptions = ["GEOMETRY=AS_WKT", "SEPARATOR=COMMA"]

    try:
        result = QgsVectorFileWriter.writeAsVectorFormatV3(
            layer, path, QgsCoordinateTransformContext(), options
        )
        err_code = result[0]
        err_msg = result[1] if len(result) > 1 else ""
    except AttributeError:
        # Older QGIS fallback
        err_code, err_msg = QgsVectorFileWriter.writeAsVectorFormat(
            layer, path, "UTF-8", layer.crs(), "CSV",
            onlySelected=only_selected,
            layerOptions=["GEOMETRY=AS_WKT", "SEPARATOR=COMMA"],
        )

    if err_code == QgsVectorFileWriter.NoError:
        QMessageBox.information(dialog, "Export complete",
                                f"Exported to:\n{path}")
    else:
        QMessageBox.warning(dialog, "Export failed",
                            f"Error {err_code}: {err_msg}")


def inject_buttons(dialog, layer, iface=None):
    if getattr(dialog, _INJECTED_ATTR, False):
        return

    toolbars = dialog.findChildren(QToolBar)
    _log(f"inject: toolbars={len(toolbars)} layer={layer.name() if layer else None} "
         f"gtype={layer.geometryType() if layer else None}")
    if not toolbars:
        return
    toolbar = next((tb for tb in toolbars if tb.isVisible()), toolbars[0])

    if layer is not None and hasattr(layer, "geometryType"):
        gtype = layer.geometryType()
        area_enabled   = gtype == QgsWkbTypes.PolygonGeometry
        length_enabled = gtype == QgsWkbTypes.LineGeometry
        point_enabled  = gtype == QgsWkbTypes.PointGeometry
    else:
        area_enabled = length_enabled = point_enabled = True

    toolbar.addSeparator()

    specs = [
        ("area",   "Area",   "area.svg",   "Add virtual area field (polygon layers)",   area_enabled),
        ("length", "Length", "length.svg", "Add virtual length field (line layers)",    length_enabled),
        ("x",      "X",      "x.svg",      "Add virtual X-coordinate field (point layers)", point_enabled),
        ("y",      "Y",      "y.svg",      "Add virtual Y-coordinate field (point layers)", point_enabled),
    ]

    for mode, label, icon_name, tooltip, enabled in specs:
        act = QAction(_icon(icon_name), label, dialog)
        act.setToolTip(tooltip)
        act.setEnabled(enabled)
        act.triggered.connect(
            lambda checked=False, d=dialog, m=mode: _on_click(d, iface, m)
        )
        toolbar.addAction(act)

    toolbar.addSeparator()
    export_action = QAction(_icon("export.svg"), "Export CSV", dialog)
    export_action.setToolTip("Export attribute table to CSV")
    export_action.triggered.connect(
        lambda checked=False, d=dialog: _on_export_csv(d, iface)
    )
    toolbar.addAction(export_action)

    setattr(dialog, _INJECTED_ATTR, True)
    _log(f"Injected. area={area_enabled} length={length_enabled} point={point_enabled}")
