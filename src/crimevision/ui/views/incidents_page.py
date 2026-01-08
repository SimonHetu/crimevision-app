from PySide6.QtCore import Qt, QPoint # Import des constantes Qt

# Import des constantes Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QPushButton, QMessageBox, QMenu, QComboBox, QLineEdit, QSpinBox
)

# Import des widgets nécessaires
from crimevision.core.services.incident_service import IncidentService

# Service qui fournit la liste des PDQs
from crimevision.core.services.pdq_service import PdqService


# Page "Incidents" : écran qui affiche les incidents avec filtres, tableau et actions contextuelles
class IncidentsPage(QWidget):
    def __init__(self):
        super().__init__()

        # Initialisation des services utilisés par cette page
        self.service = IncidentService()
        self.pdq_service = PdqService()

        # Layout vertical principal qui organise toute la page
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Incidents"))

        # Ligne de filtres (barre horizontale) pour affiner la liste des incidents
        filters = QHBoxLayout()

        # Combo PDQ : permet de filtrer par poste de quartier (ou "All PDQs")
        self.pdq_combo = QComboBox()
        self.pdq_combo.addItem("Tout les PDQs", None)

        # Combo période : filtre temporel (tout, 24h, 7 jours, 30 jours)
        self.period_combo = QComboBox()
        self.period_combo.addItem("Tout", "all")
        self.period_combo.addItem("24h", "day")
        self.period_combo.addItem("7 jours", "week")
        self.period_combo.addItem("30 jours", "month")
        
        # Champ type : filtre optionnel sur la catégorie exacte de l'incident
        self.type_in = QLineEdit()
        self.type_in.setPlaceholderText("Categorie (optionel)")

        # Limite : contrôle du nombre maximum de lignes chargées depuis la base
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(10, 5000)
        self.limit_spin.setValue(200)

        # Bouton refresh : recharge les incidents selon les filtres actuels
        self.btn_refresh = QPushButton("Reload")

         # Assemblage de la barre de filtres dans l'ordre d'utilisation
        filters.addWidget(QLabel("PDQ:"))
        filters.addWidget(self.pdq_combo)
        filters.addWidget(QLabel("Période:"))
        filters.addWidget(self.period_combo)
        filters.addWidget(self.type_in, 1)
        filters.addWidget(QLabel("Limite:"))
        filters.addWidget(self.limit_spin)
        filters.addWidget(self.btn_refresh)

        # Ajout de la barre de filtres à la page
        layout.addLayout(filters)

        # Tableau principal qui affiche les incidents sous forme de lignes/colonnes
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Date", "PDQ", "Category", "TimePeriod", "Source", "SourceId", "X", "Y", "Lon/Lat"]
        )

        # Configuration du tableau : sélection de lignes, une seule ligne à la fois, et aucune édition
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        # Activation du menu contextuel (clic droit) sur le tableau
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        # Connexions des événements : chaque action/filtres déclenche un refresh
        self.btn_refresh.clicked.connect(self.refresh)
        self.pdq_combo.currentIndexChanged.connect(self.refresh)
        self.period_combo.currentIndexChanged.connect(self.refresh)
        self.type_in.returnPressed.connect(self.refresh)

        # Chargement initial des PDQs dans la liste déroulante + premier affichage des incidents
        self._load_pdqs()
        self.refresh()

    # Charge les PDQs depuis la base pour remplir la combo de filtre
    def _load_pdqs(self):
        try:
            pdqs = self.pdq_service.list_pdqs(limit=500)
        except Exception:
            pdqs = []

        for p in pdqs:
            self.pdq_combo.addItem(f'{p["id"]} - {p.get("name","")}', int(p["id"]))

    # Récupère l'ID de l'incident sélectionné (stocké dans Qt.UserRole de la colonne ID)
    def _selected_incident_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if not item:
            return None
        return item.data(Qt.UserRole)

    # Recharge la liste d'incidents en appliquant les filtres et remplit le tableau
    def refresh(self):

        # Lecture des filtres actuels dans l'interface
        pdq_id = self.pdq_combo.currentData()
        period = self.period_combo.currentData()
        type_filter = self.type_in.text().strip()
        limit = int(self.limit_spin.value())

        # Appel au service pour obtenir la liste filtrée; affiche une erreur si la DB échoue
        try:
            incidents = self.service.list_incidents(
                limit=limit,
                pdq_id=pdq_id,
                period=period,
                type_filter=type_filter,
            )

        except Exception as e:
            QMessageBox.critical(self, "DB Error", str(e))
            return

        # Remplissage du tableau ligne par ligne à partir des dictionnaires retournés par le service
        self.table.setRowCount(len(incidents))
        for r, i in enumerate(incidents):
            inc_id = int(i["id"])

            # Colonne ID : on affiche le texte + on garde la vraie valeur dans UserRole pour les actions
            id_item = QTableWidgetItem(str(inc_id))
            id_item.setData(Qt.UserRole, inc_id)
            self.table.setItem(r, 0, id_item)

            # Colonne Date : formatage humain de la date si elle existe
            dt = i.get("date")
            dt_text = dt.strftime("%Y-%m-%d %H:%M") if dt else ""

            # Colonnes de données principales (PDQ, catégorie, période, provenance, coordonnées)
            self.table.setItem(r, 1, QTableWidgetItem(dt_text))
            self.table.setItem(r, 2, QTableWidgetItem("" if i.get("pdqId") is None else str(i["pdqId"])))
            self.table.setItem(r, 3, QTableWidgetItem(i.get("category") or ""))
            self.table.setItem(r, 4, QTableWidgetItem(str(i.get("timePeriod") or "")))
            self.table.setItem(r, 5, QTableWidgetItem(i.get("source") or ""))
            self.table.setItem(r, 6, QTableWidgetItem("" if i.get("sourceId") is None else str(i["sourceId"])))
            self.table.setItem(r, 7, QTableWidgetItem("" if i.get("x") is None else str(i["x"])))
            self.table.setItem(r, 8, QTableWidgetItem("" if i.get("y") is None else str(i["y"])))

            # Colonne Lon/Lat : concatène longitude et latitude pour un affichage compact
            lon = "" if i.get("longitude") is None else str(i["longitude"])
            lat = "" if i.get("latitude") is None else str(i["latitude"])
            self.table.setItem(r, 9, QTableWidgetItem(f"{lon} / {lat}"))

        # Ajuste automatiquement la largeur des colonnes selon leur contenu
        self.table.resizeColumnsToContents()

    # Affiche un menu contextuel (clic droit) avec actions rapides
    def show_context_menu(self, pos: QPoint):
        menu = QMenu(self)
        act_refresh = menu.addAction("Reload")
        menu.addSeparator()

        # Action copie : exporte la ligne sélectionnée en texte (utile pour debug/partage)
        act_copy = menu.addAction("Copier la selection en texte")

        # Action suppression : supprime l'incident sélectionné (action sensible)
        act_delete = menu.addAction("Delete selection… (Prudence)")

        # Active/désactive les actions selon si une ligne est sélectionnée
        has_sel = self._selected_incident_id() is not None
        act_copy.setEnabled(has_sel)
        act_delete.setEnabled(has_sel)

        # Exécute le menu et déclenche l'action choisie
        chosen = menu.exec(self.table.viewport().mapToGlobal(pos))
        if chosen == act_refresh:
            self.refresh()
        elif chosen == act_copy:
            self.copy_selected()
        elif chosen == act_delete:
            self.delete_selected()

    # Copie la ligne sélectionnée dans le presse-papier sous forme de texte "Colonne: Valeur"
    def copy_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        parts = []
        for c in range(self.table.columnCount()):
            parts.append(self.table.horizontalHeaderItem(c).text() + ": " + (self.table.item(row, c).text() if self.table.item(row, c) else ""))
        text = " | ".join(parts)

        # Accès au presse-papier Qt (protégé par try/except pour éviter un crash)
        try:
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(text)
        except Exception:
            pass
    
    # Supprime l'incident sélectionné après confirmation utilisateur
    def delete_selected(self):
        inc_id = self._selected_incident_id()
        if inc_id is None:
            return

        # Confirmation pour éviter une suppression accidentelle
        confirm = QMessageBox.question(
            self,
            "Delete incident",
            f"Delete incident #{inc_id}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        # Appel au service pour supprimer, puis refresh de la liste
        try:
            self.service.delete_incident(inc_id)
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Delete failed", str(e))
