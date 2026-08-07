from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QRadioButton, QDialogButtonBox, QLabel, QButtonGroup
)


class UnitDialog(QDialog):
    """Small dialog letting the user pick a unit for area or length."""

    AREA_UNITS = [("Square meters (m²)", "m2"),
                  ("Square kilometers (km²)", "km2")]
    LENGTH_UNITS = [("Meters (m)", "m"),
                    ("Kilometers (km)", "km")]

    def __init__(self, mode, parent=None):
        super().__init__(parent)
        self.mode = mode  # "area" or "length"
        self._selected = None

        self.setWindowTitle("Select unit")
        layout = QVBoxLayout(self)

        label_text = "Choose area unit:" if mode == "area" else "Choose length unit:"
        layout.addWidget(QLabel(label_text))

        self._group = QButtonGroup(self)
        units = self.AREA_UNITS if mode == "area" else self.LENGTH_UNITS
        self._buttons = []
        for i, (label, key) in enumerate(units):
            rb = QRadioButton(label)
            if i == 0:
                rb.setChecked(True)
            self._group.addButton(rb, i)
            layout.addWidget(rb)
            self._buttons.append((rb, key))

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._on_accept)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)

    def _on_accept(self):
        for rb, key in self._buttons:
            if rb.isChecked():
                self._selected = key
                break
        self.accept()

    def selected_unit(self):
        return self._selected
