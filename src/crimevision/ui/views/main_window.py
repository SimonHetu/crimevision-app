# Import des composants Qt nécessaires à la fenêtre principale et à la navigation
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QStackedWidget,
)

# Import des différentes pages de l'application
from .dashboard_page import DashboardPage
from .users_page import UsersPage
from .pdq_page import PdqPage
from .incidents_page import IncidentsPage


# Fenêtre principale de l'application CrimeVision
# Elle contient la structure globale (sidebar + pages)
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Configuration de base de la fenêtre (titre et dimensions)
        self.setWindowTitle("CrimeVision")
        self.resize(1500, 1000)

        # Widget central pour une QMainWindow
        # Il sert de conteneur racine pour tous les layouts
        central = QWidget()
        self.setCentralWidget(central)

        # Layout horizontal principal : sidebar à gauche, contenu à droite
        root_layout = QHBoxLayout(central)

        # Création de la barre latérale (navigation)
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(self.sidebar)

        # Configuration de l'espacement et des marges de la sidebar
        sidebar_layout.setSpacing(6)
        sidebar_layout.setContentsMargins(8, 8, 8, 8)

         # Boutons de navigation
        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_users = QPushButton("Users")
        self.btn_pdq = QPushButton("PDQ")
        self.btn_incidents = QPushButton("Incidents")

        # Ajout des boutons dans la sidebar
        sidebar_layout.addWidget(self.btn_dashboard)
        sidebar_layout.addWidget(self.btn_users)
        sidebar_layout.addWidget(self.btn_pdq)
        sidebar_layout.addWidget(self.btn_incidents)

        # Espace flexible pour pousser les boutons vers le haut
        sidebar_layout.addStretch()

        # Conteneur de pages empilées (une seule visible à la fois)
        self.stack = QStackedWidget()

        # Instanciation des différentes pages de l'application
        self.dashboard_page = DashboardPage()
        self.users_page = UsersPage()
        self.pdq_page = PdqPage()
        self.incidents_page = IncidentsPage()

        # Ajout des pages dans le conteneur empilé
        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.users_page)
        self.stack.addWidget(self.pdq_page)
        self.stack.addWidget(self.incidents_page)

        # Assemblage final : sidebar + zone de contenu
        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(self.stack)

        # Placeholder pour une future page de connexion
        self.login_page = None

        # Connexion des boutons de navigation au changement de page
        self.btn_dashboard.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.dashboard_page))
        
        self.btn_users.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.users_page))
        
        self.btn_pdq.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.pdq_page))
        
        self.btn_incidents.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.incidents_page))

    # Ajoute dynamiquement une page de connexion et connecte le signal de login
    def set_login_page(self, login_page):
        """Add login page to stack and wire fake login."""
        self.login_page = login_page
        self.stack.addWidget(self.login_page)
        self.login_page.loginRequested.connect(self._on_login_requested)

    # Affiche la page de connexion et masque la sidebar
    def show_login(self):
        """Show login and hide sidebar."""
        if self.login_page is not None:
            self.sidebar.setVisible(False)
            self.stack.setCurrentWidget(self.login_page)

    # Gestion simplifiée du succès de connexion
    def _on_login_requested(self, username: str, password: str):
        """Fake login success -> show dashboard and sidebar."""
        self.sidebar.setVisible(True)
        self.stack.setCurrentWidget(self.dashboard_page)
