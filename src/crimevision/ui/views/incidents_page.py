from PySide6.QtCore import Qt, QPoint

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QPushButton, QMessageBox, QMenu, QComboBox, QSpinBox
)

from crimevision.core.services.incident_service import IncidentService
from crimevision.core.services.pdq_service import PdqService
from crimevision.ui.views.incident_detail_dialog import IncidentDetailDialog


class IncidentsPage(QWidget):
    def __init__(self):
        super().__init__()

        self.service = IncidentService()
        self.pdq_service = PdqService()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Incidents"))

        # -------------------------
        # Filters bar
        # -------------------------
        filters = QHBoxLayout()

        # PDQ filter
        self.pdq_combo = QComboBox()
        self.pdq_combo.addItem("Tout les PDQs", None)

        # Period filter
        self.period_combo = QComboBox()
        self.period_combo.addItem("Tout", "all")
        self.period_combo.addItem("24h", "day")
        self.period_combo.addItem("7 jours", "week")
        self.period_combo.addItem("30 jours", "month")

        # Category dropdown (NEW)
        self.cat_combo = QComboBox()
        self.cat_combo.addItem("Toutes les catégories", "")  # empty => no filter
        self.cat_combo.setMinimumWidth(260)

        # Limit
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(10, 5000)
        self.limit_spin.setValue(200)

        # Refresh button
        self.btn_refresh = QPushButton("Reload")

        filters = QHBoxLayout()
        filters.setSpacing(10)

        # --- PDQ ---
        filters.addWidget(QLabel("PDQ:"))
        filters.addWidget(self.pdq_combo)

        # --- Période ---
        filters.addWidget(QLabel("Période:"))
        filters.addWidget(self.period_combo)

        # --- Catégorie ---
        filters.addWidget(QLabel("Catégorie:"))
        filters.addWidget(self.cat_combo)

       
        filters.addStretch(1)

        # --- Limite ---
        filters.addWidget(QLabel("Limite:"))
        filters.addWidget(self.limit_spin)
        filters.addWidget(self.btn_refresh)

        filters.addWidget(self.btn_refresh)

        layout.addLayout(filters)

        # -------------------------
        # Table
        # -------------------------
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Date", "PDQ", "Category", "TimePeriod", "Source", "SourceId", "X", "Y", "Lon/Lat"]
        )

        self.table.itemDoubleClicked.connect(lambda _: self.open_details())
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        # Context menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        # Events
        self.btn_refresh.clicked.connect(self.refresh)
        self.pdq_combo.currentIndexChanged.connect(self.refresh)
        self.period_combo.currentIndexChanged.connect(self.refresh)
        self.cat_combo.currentIndexChanged.connect(self.refresh)

        # Init data
        self._load_pdqs()
        self._load_categories()
        self.refresh()

    # -------------------------
    # Data for combos
    # -------------------------
    def _load_pdqs(self):
        try:
            pdqs = self.pdq_service.list_pdqs(limit=500)
        except Exception:
            pdqs = []

        for p in pdqs:
            self.pdq_combo.addItem(f'{p["id"]} - {p.get("name","")}', int(p["id"]))

    def _load_categories(self):
        # Keep current selection if possible
        current = self.cat_combo.currentData()

        # Reset dropdown
        self.cat_combo.blockSignals(True)
        self.cat_combo.clear()
        self.cat_combo.addItem("Toutes les catégories", "")

        try:
            cats = self.service.list_categories()
        except Exception:
            cats = []

        for c in cats:
            self.cat_combo.addItem(c, c)

        # Restore selection if still present
        if current:
            idx = self.cat_combo.findData(current)
            if idx >= 0:
                self.cat_combo.setCurrentIndex(idx)

        self.cat_combo.blockSignals(False)

    # -------------------------
    # Helpers
    # -------------------------
    def open_details(self):
        inc_id = self._selected_incident_id()
        if inc_id is None:
            return
        dlg = IncidentDetailDialog(incident_id=inc_id, parent=self)
        dlg.exec()

    def _selected_incident_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if not item:
            return None
        return item.data(Qt.UserRole)

    # -------------------------
    # Refresh table
    # -------------------------
    def refresh(self):
        pdq_id = self.pdq_combo.currentData()
        period = self.period_combo.currentData()
        category = (self.cat_combo.currentData() or "").strip()
        limit = int(self.limit_spin.value())

        try:
            incidents = self.service.list_incidents(
                limit=limit,
                pdq_id=pdq_id,
                period=period,
                type_filter=category,   # <- uses your existing exact match filter
            )
        except Exception as e:
            QMessageBox.critical(self, "DB Error", str(e))
            return

        self.table.setRowCount(len(incidents))
        for r, i in enumerate(incidents):
            inc_id = int(i["id"])

            id_item = QTableWidgetItem(str(inc_id))
            id_item.setData(Qt.UserRole, inc_id)
            self.table.setItem(r, 0, id_item)

            dt = i.get("date")
            dt_text = dt.strftime("%Y-%m-%d %H:%M") if dt else ""

            self.table.setItem(r, 1, QTableWidgetItem(dt_text))
            self.table.setItem(r, 2, QTableWidgetItem("" if i.get("pdqId") is None else str(i["pdqId"])))
            self.table.setItem(r, 3, QTableWidgetItem(i.get("category") or ""))
            self.table.setItem(r, 4, QTableWidgetItem(str(i.get("timePeriod") or "")))
            self.table.setItem(r, 5, QTableWidgetItem(i.get("source") or ""))
            self.table.setItem(r, 6, QTableWidgetItem("" if i.get("sourceId") is None else str(i["sourceId"])))
            self.table.setItem(r, 7, QTableWidgetItem("" if i.get("x") is None else str(i["x"])))
            self.table.setItem(r, 8, QTableWidgetItem("" if i.get("y") is None else str(i["y"])))

            lon = "" if i.get("longitude") is None else str(i["longitude"])
            lat = "" if i.get("latitude") is None else str(i["latitude"])
            self.table.setItem(r, 9, QTableWidgetItem(f"{lon} / {lat}"))

        self.table.resizeColumnsToContents()

    # -------------------------
    # Context menu
    # -------------------------
    def show_context_menu(self, pos: QPoint):
        menu = QMenu(self)
        act_refresh = menu.addAction("Reload")
        menu.addSeparator()

        act_copy = menu.addAction("Copier la selection en texte")
        act_delete = menu.addAction("Delete selection… (Prudence)")

        has_sel = self._selected_incident_id() is not None
        act_copy.setEnabled(has_sel)
        act_delete.setEnabled(has_sel)

        chosen = menu.exec(self.table.viewport().mapToGlobal(pos))
        if chosen == act_refresh:
            self.refresh()
        elif chosen == act_copy:
            self.copy_selected()
        elif chosen == act_delete:
            self.delete_selected()

    def copy_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        parts = []
        for c in range(self.table.columnCount()):
            header = self.table.horizontalHeaderItem(c).text()
            val = self.table.item(row, c).text() if self.table.item(row, c) else ""
            parts.append(f"{header}: {val}")
        text = " | ".join(parts)

        try:
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(text)
        except Exception:
            pass

    def delete_selected(self):
        inc_id = self._selected_incident_id()
        if inc_id is None:
            return

        confirm = QMessageBox.question(
            self,
            "Delete incident",
            f"Delete incident #{inc_id}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            self.service.delete_incident(inc_id)
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Delete failed", str(e))