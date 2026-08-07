from qgis.PyQt.QtWidgets import QToolBar, QMessageBox
try:
    from qgis.PyQt.QtGui import QAction  # Qt6
except ImportError:
    from qgis.PyQt.QtWidgets import QAction  # Qt5
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsWkbTypes, QgsMessageLog, Qgis, QgsProject

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
    """Best-effort fresh layer lookup at click time."""
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


def _on_click(dialog, iface, mode):
    layer = _resolve_layer(dialog, iface)
    if layer is None or not hasattr(layer, "geometryType"):
        QMessageBox.warning(dialog, "No layer",
                            "Could not determine the layer for this attribute table.")
        return
    gtype = layer.geometryType()
    if mode == "area" and gtype != QgsWkbTypes.PolygonGeometry:
        QMessageBox.warning(dialog, "Wrong geometry",
                            f"Area requires a polygon layer. '{layer.name()}' is not a polygon.")
        return
    if mode == "length" and gtype != QgsWkbTypes.LineGeometry:
        QMessageBox.warning(dialog, "Wrong geometry",
                            f"Length requires a line layer. '{layer.name()}' is not a line layer.")
        return

    dlg = UnitDialog(mode, parent=dialog)
    if dlg.exec_() != dlg.Accepted:
        return
    unit = dlg.selected_unit()
    if not unit:
        return
    ok, result = add_virtual_field(layer, mode, unit)
    if ok:
        QMessageBox.information(
            dialog, "Field added",
            f"Virtual field '{result}' added to layer '{layer.name()}'."
        )
    else:
        QMessageBox.warning(
            dialog, "Failed",
            f"Could not add virtual field:\n{result}"
        )


def inject_buttons(dialog, layer, iface=None):
    if getattr(dialog, _INJECTED_ATTR, False):
        return

    toolbars = dialog.findChildren(QToolBar)
    _log(f"inject: toolbars={len(toolbars)} layer={layer.name() if layer else None} "
         f"gtype={layer.geometryType() if layer else None}")
    if not toolbars:
        return
    toolbar = next((tb for tb in toolbars if tb.isVisible()), toolbars[0])

    # Fail-safe enable logic:
    #  - If we know the geometry type, gray the button that doesn't apply.
    #  - If we DON'T know it (layer=None), leave both enabled and validate at click time.
    if layer is not None and hasattr(layer, "geometryType"):
        gtype = layer.geometryType()
        area_enabled = gtype == QgsWkbTypes.PolygonGeometry
        length_enabled = gtype == QgsWkbTypes.LineGeometry
    else:
        area_enabled = True
        length_enabled = True

    toolbar.addSeparator()

    area_action = QAction(_icon("area.svg"), "Area", dialog)
    area_action.setToolTip("Add virtual area field (polygon layers)")
    area_action.setEnabled(area_enabled)
    area_action.triggered.connect(lambda checked=False, d=dialog: _on_click(d, iface, "area"))
    toolbar.addAction(area_action)

    length_action = QAction(_icon("length.svg"), "Length", dialog)
    length_action.setToolTip("Add virtual length field (line layers)")
    length_action.setEnabled(length_enabled)
    length_action.triggered.connect(lambda checked=False, d=dialog: _on_click(d, iface, "length"))
    toolbar.addAction(length_action)

    setattr(dialog, _INJECTED_ATTR, True)
    _log(f"Injected. area_enabled={area_enabled} length_enabled={length_enabled}")
