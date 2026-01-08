import sys
import os
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from dotenv import load_dotenv

from crimevision.core.db.database import init_db, close_db
from crimevision.ui.views.main_window import MainWindow
from crimevision.ui.views.login_page import LoginPage
from crimevision.ui.theme.theme_manager import apply_theme


ASSETS = Path(__file__).parent / "assets"


def main():
    load_dotenv()
    init_db()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setAttribute(Qt.AA_UseStyleSheetPropagationInWidgetStyles, True)
    app.setProperty("windowsDarkMode", True)

    icon_path = ASSETS / "crimevision_eye.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    apply_theme(app, "dark")

    win = MainWindow()


    login = LoginPage(ASSETS)
    win.set_login_page(login)
    win.show_login()

    win.show()

    code = app.exec()

    close_db()
    sys.exit(code)


if __name__ == "__main__":
    main()
