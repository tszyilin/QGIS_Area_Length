from qgis.PyQt.QtCore import QObject, QEvent, QTimer
from qgis.PyQt.QtWidgets import QApplication, QDialog, QMainWindow
from qgis.core import QgsMessageLog, Qgis, QgsProject

from .toolbar_buttons import inject_buttons


def _log(msg):
    QgsMessageLog.logMessage(str(msg), "AreaLength", Qgis.Info)


def _looks_like_attr_table(widget):
    try:
        cls = widget.metaObject().className()
    except Exception:
        return False
    if "AttributeTable" in cls:
        return True
    name = widget.objectName() or ""
    return "AttributeTable" in name


def _extract_layer_from_title(widget):
    title = widget.windowTitle() or ""
    # Strip common suffixes.
    name = title
    for sep in (" — ", " – ", " - "):
        if sep in name:
            name = name.split(sep, 1)[0]
            break
    name = name.strip()
    if not name:
        return None
    for layer in QgsProject.instance().mapLayers().values():
        if layer.name() == name and hasattr(layer, "geometryType"):
            return layer
    return None


class _AttrTableWatcher(QObject):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface

    def eventFilter(self, obj, event):
        try:
            if event.type() == QEvent.Show and isinstance(obj, (QDialog, QMainWindow)):
                if _looks_like_attr_table(obj):
                    layer = _extract_layer_from_title(obj) or self.iface.activeLayer()
                    _log(f"Show: cls={obj.metaObject().className()!r} title={obj.windowTitle()!r} layer={layer.name() if layer else None}")
                    inject_buttons(obj, layer, self.iface)
        except Exception:
            import traceback
            QgsMessageLog.logMessage(traceback.format_exc(), "AreaLength", Qgis.Warning)
        return False


class AreaLengthPlugin:
    def __init__(self, iface):
        self.iface = iface
        self._watcher = None

    def initGui(self):
        self._watcher = _AttrTableWatcher(self.iface)
        QApplication.instance().installEventFilter(self._watcher)
        _log("Plugin loaded.")
        QTimer.singleShot(0, self._scan_existing)

    def _scan_existing(self):
        try:
            for w in QApplication.topLevelWidgets():
                if _looks_like_attr_table(w) and w.isVisible():
                    layer = _extract_layer_from_title(w) or self.iface.activeLayer()
                    _log(f"Scan: title={w.windowTitle()!r} layer={layer.name() if layer else None}")
                    inject_buttons(w, layer, self.iface)
        except Exception:
            import traceback
            QgsMessageLog.logMessage(traceback.format_exc(), "AreaLength", Qgis.Warning)

    def unload(self):
        if self._watcher is not None:
            QApplication.instance().removeEventFilter(self._watcher)
            self._watcher = None
