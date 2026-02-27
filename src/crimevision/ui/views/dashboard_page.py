from PySide6.QtCore import Qt # Import des constantes Qt

# Import des widgets et layouts nécessaires à l'interface du dashboard
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QListWidget, QListWidgetItem
)

# Services utilisés pour lire les données depuis la base (utilisateurs et incidents)
from crimevision.core.services.user_service import UserService
from crimevision.core.services.incident_service import IncidentService
from crimevision.core.services.auth_service import AuthService

# Fonction utilitaire qui crée une "carte" réutilisable (un bloc UI stylé avec un titre) 
def _card(title: str) -> tuple[QFrame, QVBoxLayout, QLabel]:
    # Conteneur visuel de la carte (QFrame) + nom pour le style QSS
    box = QFrame()
    box.setObjectName("card")

    # Layout interne vertical pour empiler le titre + contenu
    layout = QVBoxLayout(box)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(8)

    # Titre de la carte + nom pour le style QSS
    t = QLabel(title)
    t.setObjectName("cardTitle")
    layout.addWidget(t)

    # Retourne les éléments pour permettre d'ajouter du contenu dans la carte ailleurs
    return box, layout, t

# KPI = Key Performance Indicator
# Page Dashboard : écran principal qui affiche statistiques et aperçus de données
class DashboardPage(QWidget):
    def __init__(self, auth):
        super().__init__()
        self.auth = auth

        # Initialisation des services pour récupérer les données depuis la DB
        self.user_service = UserService()
        self.incident_service = IncidentService()

        # Layout racine vertical qui organise toute la page en sections (haut/milieu/bas)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        # Titre principal de la page (stylé via QSS avec pageTitle)
        title = QLabel("CrimeVision Dashboard")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        # Rangée de KPI (cartes statistiques) en horizontal
        self.kpi_row = QHBoxLayout()
        self.kpi_row.setSpacing(10)
        root.addLayout(self.kpi_row)

        # Création des 4 KPI affichés en haut (valeurs mises à jour dans refresh())
        self.kpi_total_incidents = self._kpi("Total Incidents", "—")
        self.kpi_7d_incidents = self._kpi("Incidents (7 days)", "—")
        self.kpi_pdqs = self._kpi("PDQs", "—")
        self.kpi_users = self._kpi("Users", "—")

        # Section centrale : deux tableaux d'aperçu (incidents récents + users récents)
        mid = QHBoxLayout()
        mid.setSpacing(10)
        root.addLayout(mid, 2)

        # Carte "Incidents récents" contenant un tableau non-éditable
        inc_card, inc_layout, _ = _card("Incidents Récents")
        self.tbl_inc = QTableWidget()
        self.tbl_inc.setColumnCount(6)
        self.tbl_inc.setHorizontalHeaderLabels(["ID", "Date", "PDQ", "Category", "Lat", "Lon"])
        self.tbl_inc.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_inc.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_inc.setSelectionMode(QTableWidget.SingleSelection)
        inc_layout.addWidget(self.tbl_inc)
        mid.addWidget(inc_card, 2)

        # Carte "Users récents" contenant un tableau non-éditable
        usr_card, usr_layout, _ = _card("Users Recents")
        self.tbl_usr = QTableWidget()
        self.tbl_usr.setColumnCount(5)
        self.tbl_usr.setHorizontalHeaderLabels(["ID", "Email", "Name", "Pseudo", "Created"])
        self.tbl_usr.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_usr.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_usr.setSelectionMode(QTableWidget.SingleSelection)
        usr_layout.addWidget(self.tbl_usr)
        mid.addWidget(usr_card, 2)

        # Section du bas : deux listes de classement (Top PDQs et Top catégories)
        bot = QHBoxLayout()
        bot.setSpacing(10)
        root.addLayout(bot, 1)

        # Carte "Top PDQs" avec une liste simple (PDQ + nombre d'incidents)
        pdq_card, pdq_layout, _ = _card("Top PDQs (7 jours)")
        self.list_pdq = QListWidget()
        pdq_layout.addWidget(self.list_pdq)
        bot.addWidget(pdq_card, 1)

        # Carte "Top catégories" avec une liste simple (catégorie + nombre d'incidents)
        cat_card, cat_layout, _ = _card("Top Categories (7 jours)")
        self.list_cat = QListWidget()
        cat_layout.addWidget(self.list_cat)
        bot.addWidget(cat_card, 1)

        # Chargement initial des données dans le dashboard
        self.refresh()

    
    # Méthode utilitaire pour créer une carte KPI (titre + valeur) et la placer dans la rangée KPI
    def _kpi(self, label: str, value: str) -> QLabel:
        card, layout, _ = _card(label)
        v = QLabel(value)
        v.setObjectName("kpiValue")
        layout.addWidget(v)
        self.kpi_row.addWidget(card, 1)
        return v

    # Recharge toutes les données affichées sur le dashboard (KPIs, tableaux, classements)
    def refresh(self):
        # Section KPI : calcule les statistiques globales et sur 7 jours
        # --- KPI: total incidents
        try:
            total = self.incident_service.count_all()
        except Exception:
            total = None

        # --- KPI: incidents 7 jours
        try:
            last_7d = self.incident_service.count_since_days(7)
        except Exception:
            last_7d = None

        # --- KPI: users
        try:
            users = self.user_service.count_users()
        except Exception:
            users = None

        # --- KPI: PDQs
        try:
            pdq_count = self.incident_service.count_unique_pdqs()
        except Exception:
            pdq_count = None

        self.kpi_total_incidents.setText("—" if total is None else str(total))
        self.kpi_7d_incidents.setText("—" if last_7d is None else str(last_7d))
        self.kpi_users.setText("—" if users is None else str(users))
        self.kpi_pdqs.setText("—" if pdq_count is None else str(pdq_count))


        # Section incidents récents : charge les derniers incidents et remplit le tableau
        try:
            rows = self.incident_service.list_incidents(
                limit=12, pdq_id=None, period="all", type_filter="", search=""
            )
            
            self.tbl_inc.setRowCount(len(rows))
            for r, i in enumerate(rows):
                self._set(self.tbl_inc, r, 0, i.get("id"))
                dt = i.get("date")
                self._set(self.tbl_inc, r, 1, dt.strftime("%Y-%m-%d %H:%M") if dt else "")
                self._set(self.tbl_inc, r, 2, "" if i.get("pdqId") is None else i.get("pdqId"))
                self._set(self.tbl_inc, r, 3, i.get("category") or "")
                self._set(self.tbl_inc, r, 4, i.get("latitude") or "")
                self._set(self.tbl_inc, r, 5, i.get("longitude") or "")

            # Ajuste automatiquement la largeur des colonnes selon leur contenu
            self.tbl_inc.resizeColumnsToContents()
        
        # En cas d'erreur, on affiche un message d'erreur dans le tableau au lieu de planter l'app
        except Exception as e:
            self.tbl_inc.setRowCount(1)
            self._set(self.tbl_inc, 0, 0, "Error")
            self._set(self.tbl_inc, 0, 1, str(e))

        # Section users récents : charge les derniers utilisateurs et remplit le tableau
        try:
            rows = self.user_service.list_recent_users(limit=12)
            self.tbl_usr.setRowCount(len(rows))
            for r, u in enumerate(rows):
                self._set(self.tbl_usr, r, 0, u.get("id"))
                self._set(self.tbl_usr, r, 1, u.get("email") or "")
                self._set(self.tbl_usr, r, 2, u.get("name") or "")
                self._set(self.tbl_usr, r, 3, u.get("pseudo") or "")
                dt = u.get("createdAt")
                self._set(self.tbl_usr, r, 4, dt.strftime("%Y-%m-%d %H:%M") if dt else "")
            self.tbl_usr.resizeColumnsToContents()
        
        # En cas d'erreur, on affiche un message d'erreur dans le tableau au lieu de planter l'app
        except Exception as e:
            self.tbl_usr.setRowCount(1)
            self._set(self.tbl_usr, 0, 0, "Error")
            self._set(self.tbl_usr, 0, 1, str(e))

        # Section Top PDQs : affiche les PDQs les plus touchés sur 7 jours
        try:
            self.list_pdq.clear()
            for x in self.incident_service.top_pdqs(days=7, limit=8):
                self.list_pdq.addItem(f"PDQ {x['pdqId']} — {x['count']}")
        except Exception as e:
            self.list_pdq.clear()
            self.list_pdq.addItem(f"Error: {e}")

        # Section Top catégories : affiche les catégories les plus fréquentes sur 7 jours
        try:
            self.list_cat.clear()
            for x in self.incident_service.top_categories(days=7, limit=10):
                self.list_cat.addItem(f"{x['category']} — {x['count']}")
        except Exception as e:
            self.list_cat.clear()
            self.list_cat.addItem(f"Error: {e}")

    # Helper pour écrire une valeur dans une cellule de tableau en la rendant non-éditable
    def _set(self, table: QTableWidget, row: int, col: int, value):
        item = QTableWidgetItem("" if value is None else str(value))
        item.setFlags(item.flags() ^ Qt.ItemIsEditable)
        table.setItem(row, col, item)