from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
)

from .dashboard_page import DashboardPage
from .users_page import UsersPage
from .pdq_page import PdqPage
from .incidents_page import IncidentsPage
from .imports_page import ImportsPage
from .stats_page import StatsPage

from crimevision.ui.theme.glow_button import GlowButton

from crimevision.core.services.auth_service import AuthService


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CrimeVision")
        self.resize(1500, 1000)

        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)

        # ------------------------------------------------------------
        # Sidebar
        # ------------------------------------------------------------
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setSpacing(6)
        sidebar_layout.setContentsMargins(8, 8, 8, 8)

        # Buttons
        self.btn_dashboard = GlowButton("Dashboard")
        self.btn_users = GlowButton("Users")
        self.btn_pdq = GlowButton("PDQ")
        self.btn_incidents = GlowButton("Incidents")
        self.btn_imports = GlowButton("Imports")
        self.btn_stats = GlowButton("Stats")

        self._nav_buttons = [
            self.btn_dashboard,
            self.btn_users,
            self.btn_pdq,
            self.btn_incidents,
            self.btn_imports,
            self.btn_stats,
        ]

        for btn in self._nav_buttons:
            btn.setCheckable(True)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        # ------------------------------------------------------------
        # Pages (stack)
        # ------------------------------------------------------------
        self.stack = QStackedWidget()

        self.auth = AuthService(api_base="https://crimevision-backend.vercel.app/")

        self.dashboard_page = DashboardPage(auth=self.auth)
        self.users_page = UsersPage()
        self.pdq_page = PdqPage()
        self.incidents_page = IncidentsPage()
        self.imports_page = ImportsPage()
        self.stats_page = StatsPage()

        self.sidebar.setVisible(False)

        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.users_page)
        self.stack.addWidget(self.pdq_page)
        self.stack.addWidget(self.incidents_page)
        self.stack.addWidget(self.imports_page)
        self.stack.addWidget(self.stats_page)

        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(self.stack)

        self.login_page = None

        # ------------------------------------------------------------
        # Navigation wiring
        # ------------------------------------------------------------
        self.btn_dashboard.clicked.connect(
            lambda: self._switch_page(self.dashboard_page, self.btn_dashboard)
        )
        self.btn_users.clicked.connect(
            lambda: self._switch_page(self.users_page, self.btn_users)
        )
        self.btn_pdq.clicked.connect(
            lambda: self._switch_page(self.pdq_page, self.btn_pdq)
        )
        self.btn_incidents.clicked.connect(
            lambda: self._switch_page(self.incidents_page, self.btn_incidents)
        )
        self.btn_imports.clicked.connect(
            lambda: self._switch_page(self.imports_page, self.btn_imports)
        )
        self.btn_stats.clicked.connect(
            lambda: self._switch_page(self.stats_page, self.btn_stats)
        )

        # Default page
        self._switch_page(self.dashboard_page, self.btn_dashboard)

    # ------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------
    def _set_active_button(self, active_btn):
        for btn in self._nav_buttons:
            btn.setChecked(btn is active_btn)

    def _switch_page(self, page, button):
        self.stack.setCurrentWidget(page)
        self._set_active_button(button)

        if page is getattr(self, "stats_page", None):
            try:
                self.stats_page.refresh()
            except Exception:
                pass

    # ------------------------------------------------------------
    # Login / Auth
    # ------------------------------------------------------------
    def set_login_page(self, login_page):
        self.login_page = login_page
        self.stack.addWidget(self.login_page)
        self.login_page.loginRequested.connect(self._on_login_requested)

    def show_login(self):
        if self.login_page is not None:
            self.sidebar.setVisible(False)
            self.stack.setCurrentWidget(self.login_page)

    def _on_login_requested(self, username: str, password: str):
        try:
            # (optionnel) clear message
            if self.login_page and hasattr(self.login_page, "set_error"):
                self.login_page.set_error("")

            # ✅ vrai login admin (backend)
            self.auth.login_admin(username, password)

            # ✅ succès
            self.sidebar.setVisible(True)
            self.stack.setCurrentWidget(self.dashboard_page)
            self._set_active_button(self.btn_dashboard)

            # force reload
            if hasattr(self.dashboard_page, "refresh"):
                self.dashboard_page.refresh()
            elif hasattr(self.dashboard_page, "load"):
                self.dashboard_page.load()

        except Exception as e:
            # ❌ échec : rester sur login + afficher l'erreur
            self.sidebar.setVisible(False)
            if self.login_page and hasattr(self.login_page, "set_error"):
                self.login_page.set_error(f"❌ {e}")
            self.show_login()