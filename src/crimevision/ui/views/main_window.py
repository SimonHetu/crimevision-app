from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QStackedWidget,
)

from .dashboard_page import DashboardPage
from .users_page import UsersPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CrimeVision")
        self.resize(1200, 700)

        # --- Central widget ---
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)

        # --- Sidebar ---
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(self.sidebar)

        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_users = QPushButton("Users")

        sidebar_layout.addWidget(self.btn_dashboard)
        sidebar_layout.addWidget(self.btn_users)
        sidebar_layout.addStretch()

        # --- Pages stack ---
        self.stack = QStackedWidget()

        self.dashboard_page = DashboardPage()
        self.users_page = UsersPage()

        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.users_page)

        # --- Assemble ---
        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(self.stack)

        # --- Login page placeholder ---
        self.login_page = None

        # --- Navigation ---
        self.btn_dashboard.clicked.connect(lambda: self.stack.setCurrentWidget(self.dashboard_page))
        self.btn_users.clicked.connect(lambda: self.stack.setCurrentWidget(self.users_page))

    def set_login_page(self, login_page):
        """Add login page to stack and wire fake login."""
        self.login_page = login_page
        self.stack.addWidget(self.login_page)
        self.login_page.loginRequested.connect(self._on_login_requested)

    def show_login(self):
        """Show login and hide sidebar."""
        if self.login_page is not None:
            self.sidebar.setVisible(False)
            self.stack.setCurrentWidget(self.login_page)

    def _on_login_requested(self, username: str, password: str):
        """Fake login success -> show dashboard and sidebar."""
        self.sidebar.setVisible(True)
        self.stack.setCurrentWidget(self.dashboard_page)
