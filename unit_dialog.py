from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QRadioButton, QDialogButtonBox,
    QLabel, QButtonGroup, QSpinBox, QFrame
)


class UnitDialog(QDialog):
    """Dialog: pick unit (for area/length) + decimal precision."""

    UNITS = {
        "area":   [("Square meters (m²)", "m2"),
                   ("Square kilometers (km²)", "km2")],
        "length": [("Meters (m)", "m"),
                   ("Kilometers (km)", "km")],
        # x and y: no unit choice (layer CRS)
    }

    TITLES = {
        "area":   "Choose area unit:",
        "length": "Choose length unit:",
        "x":      "Add X coordinate (layer CRS)",
        "y":      "Add Y coordinate (layer CRS)",
    }

    DEFAULT_DECIMALS = 3

    def __init__(self, mode, parent=None):
        super().__init__(parent)
        self.mode = mode
        self._selected = None
        self._decimals = self.DEFAULT_DECIMALS

        self.setWindowTitle("Add virtual field")
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(self.TITLES.get(mode, mode)))

        self._buttons = []
        units = self.UNITS.get(mode)
        if units:
            self._group = QButtonGroup(self)
            for i, (label, key) in enumerate(units):
                rb = QRadioButton(label)
                if i == 0:
                    rb.setChecked(True)
                self._group.addButton(rb, i)
                layout.addWidget(rb)
                self._buttons.append((rb, key))

            divider = QFrame()
            divider.setFrameShape(QFrame.HLine)
            divider.setFrameShadow(QFrame.Sunken)
            layout.addWidget(divider)

        dec_row = QHBoxLayout()
        dec_row.addWidget(QLabel("Decimal places:"))
        self._dec_spin = QSpinBox()
        self._dec_spin.setRange(0, 10)
        self._dec_spin.setValue(self.DEFAULT_DECIMALS)
        dec_row.addWidget(self._dec_spin)
        dec_row.addStretch(1)
        layout.addLayout(dec_row)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._on_accept)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)

    def _on_accept(self):
        for rb, key in self._buttons:
            if rb.isChecked():
                self._selected = key
                break
        self._decimals = self._dec_spin.value()
        self.accept()

    def selected_unit(self):
        # None for x/y modes.
        return self._selected

    def decimals(self):
        return self._decimals
