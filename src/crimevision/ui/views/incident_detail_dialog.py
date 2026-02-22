from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QDialogButtonBox,
    QMessageBox,
)

from crimevision.core.services.incident_service import IncidentService
from crimevision.core.services.pdq_service import PdqService


class IncidentDetailDialog(QDialog):
    """
    Dialog read-only: shows full incident details.
    - Loads incident by id
    - Optionally loads PDQ info if pdqId exists
    """

    def __init__(self, *, incident_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Incident #{incident_id}")
        self.setModal(True)

        self._incident_id = incident_id
        self._incident_service = IncidentService()
        self._pdq_service = PdqService()

        root = QVBoxLayout(self)

        title = QLabel(f"Incident details — ID {incident_id}")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        self.form = QFormLayout()
        root.addLayout(self.form)

        # Create labels once (so we can setText later)
        self._fields: dict[str, QLabel] = {}
        for key in [
            "Date",
            "Category",
            "TimePeriod",
            "PDQ",
            "Source",
            "SourceId",
            "X",
            "Y",
            "Latitude",
            "Longitude",
            "PDQ Name",
            "PDQ Address",
            "PDQ CityCode",
            "PDQ Lat",
            "PDQ Lon",
        ]:
            lbl = QLabel("—")
            lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self._fields[key] = lbl
            self.form.addRow(key, lbl)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        root.addWidget(buttons)

        self._load()

    def _set(self, key: str, value):
        self._fields[key].setText("—" if value is None or value == "" else str(value))

    def _load(self):
        try:
            inc = self._incident_service.get_incident_by_id(self._incident_id)
            if not inc:
                QMessageBox.warning(self, "Not found", "Incident not found.")
                self.reject()
                return
        except Exception as e:
            QMessageBox.critical(self, "DB Error", str(e))
            self.reject()
            return

        dt = inc.get("date")
        dt_text = dt.strftime("%Y-%m-%d %H:%M") if dt else ""

        self._set("Date", dt_text)
        self._set("Category", inc.get("category"))
        self._set("TimePeriod", inc.get("timePeriod"))
        self._set("PDQ", inc.get("pdqId"))
        self._set("Source", inc.get("source"))
        self._set("SourceId", inc.get("sourceId"))
        self._set("X", inc.get("x"))
        self._set("Y", inc.get("y"))
        self._set("Latitude", inc.get("latitude"))
        self._set("Longitude", inc.get("longitude"))

        # PDQ info (optional)
        pdq_id = inc.get("pdqId")
        if pdq_id is None:
            return

        try:
            pdq = self._pdq_service.get_pdq_by_id(int(pdq_id))
        except Exception:
            pdq = None

        if not pdq:
            return

        self._set("PDQ Name", pdq.get("name"))
        self._set("PDQ Address", pdq.get("address"))
        self._set("PDQ CityCode", pdq.get("cityCode"))
        self._set("PDQ Lat", pdq.get("latitude"))
        self._set("PDQ Lon", pdq.get("longitude"))