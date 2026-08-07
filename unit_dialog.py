from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QRadioButton, QDialogButtonBox,
    QLabel, QButtonGroup, QSpinBox, QFrame
)


class UnitDialog(QDialog):
    """Dialog: pick unit + decimal precision for the virtual field."""

    AREA_UNITS = [("Square meters (m²)", "m2"),
                  ("Square kilometers (km²)", "km2")]
    LENGTH_UNITS = [("Meters (m)", "m"),
                    ("Kilometers (km)", "km")]

    DEFAULT_DECIMALS = 3

    def __init__(self, mode, parent=None):
        super().__init__(parent)
        self.mode = mode  # "area" or "length"
        self._selected = None
        self._decimals = self.DEFAULT_DECIMALS

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
        return self._selected

    def decimals(self):
        return self._decimals
