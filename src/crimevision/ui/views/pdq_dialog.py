from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox
)

class PdqDialog(QDialog):
    def __init__(
        self,
        *,
        title: str,
        name: str = "",
        address: str = "",
        cityCode: str = "",
        latitude: str = "",
        longitude: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)

        root = QVBoxLayout(self)
        form = QFormLayout()
        root.addLayout(form)

        self.name_in = QLineEdit(name)
        self.address_in = QLineEdit(address)
        self.city_in = QLineEdit(cityCode)
        self.lat_in = QLineEdit(latitude)
        self.lon_in = QLineEdit(longitude)

        form.addRow("Name", self.name_in)
        form.addRow("Address", self.address_in)
        form.addRow("CityCode", self.city_in)
        form.addRow("Latitude", self.lat_in)
        form.addRow("Longitude", self.lon_in)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    def values(self):
        def to_int(s: str):
            s = s.strip()
            return int(s) if s else None

        def to_float(s: str):
            s = s.strip()
            return float(s) if s else None

        return dict(
            name=self.name_in.text().strip(),
            address=self.address_in.text().strip() or None,
            cityCode=to_int(self.city_in.text()),
            latitude=to_float(self.lat_in.text()),
            longitude=to_float(self.lon_in.text()),
        )
