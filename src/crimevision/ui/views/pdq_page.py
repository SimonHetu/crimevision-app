from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QPushButton, QMessageBox, QMenu, QLineEdit
)

from crimevision.core.services.pdq_service import PdqService


# Page qui affiche la liste des PDQ avec une recherche simple (lecture seule)
class PdqPage(QWidget):
    def __init__(self):
        super().__init__()
        self.service = PdqService()

        # Layout principal de la page (titre + recherche + table + boutons)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("PDQs"))

        # Barre de recherche (par id ou nom) avec actions Search et Clear
        top = QHBoxLayout()
        self.search_in = QLineEdit()
        self.search_in.setPlaceholderText("Search by PDQ id or name…")
        self.btn_search = QPushButton("Search")
        self.btn_clear = QPushButton("Clear")
        top.addWidget(self.search_in, 1)
        top.addWidget(self.btn_search)
        top.addWidget(self.btn_clear)
        layout.addLayout(top)

        # Table principale qui affiche les informations d’un PDQ (colonnes principales)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Address", "CityCode", "Lat", "Lon"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        # Rangée de boutons d’action (recharger la liste)
        btn_row = QHBoxLayout()
        self.btn_refresh = QPushButton("Reload")
        btn_row.addWidget(self.btn_refresh)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        # Connexions des interactions utilisateur (boutons + Enter) vers refresh/clear
        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_search.clicked.connect(self.refresh)
        self.btn_clear.clicked.connect(self.clear_search)
        self.search_in.returnPressed.connect(self.refresh)

        # Menu contextuel (clic droit) qui permet de rafraîchir rapidement
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        # Chargement initial des données
        self.refresh()

    # Réinitialise la recherche puis recharge la table
    def clear_search(self):
        self.search_in.setText("")
        self.refresh()
    
    # Récupère l’ID du PDQ sélectionné dans la table (ou None si rien n’est sélectionné)
    def _selected_pdq_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if not item:
            return None
        return item.data(Qt.UserRole)

    # Recharge la liste depuis la DB selon la recherche et remplit la table UI
    def refresh(self):
        try:
            pdqs = self.service.list_pdqs(limit=200, search=self.search_in.text().strip())
        except Exception as e:
            QMessageBox.critical(self, "DB Error", str(e))
            return

        self.table.setRowCount(len(pdqs))
        for r, p in enumerate(pdqs):
            pdq_id = int(p["id"])
            id_item = QTableWidgetItem(str(pdq_id))
            id_item.setData(Qt.UserRole, pdq_id)
            self.table.setItem(r, 0, id_item)

            self.table.setItem(r, 1, QTableWidgetItem(p.get("name") or ""))
            self.table.setItem(r, 2, QTableWidgetItem(p.get("address") or ""))
            self.table.setItem(r, 3, QTableWidgetItem("" if p.get("cityCode") is None else str(p["cityCode"])))
            self.table.setItem(r, 4, QTableWidgetItem("" if p.get("latitude") is None else str(p["latitude"])))
            self.table.setItem(r, 5, QTableWidgetItem("" if p.get("longitude") is None else str(p["longitude"])))

        self.table.resizeColumnsToContents()

    # Affiche un petit menu contextuel permettant de rafraîchir la liste
    def show_context_menu(self, pos: QPoint):
        menu = QMenu(self)
        act_refresh = menu.addAction("Refresh")

        chosen = menu.exec(self.table.viewport().mapToGlobal(pos))
        if chosen == act_refresh:
            self.refresh()



  