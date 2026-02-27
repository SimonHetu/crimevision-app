
import sys

import os
from pathlib import Path

from PySide6.QtWidgets import QApplication

# Options globales Qt (styles, attributs)
from PySide6.QtCore import Qt

# Gestion de l’icône de l’application
from PySide6.QtGui import QIcon

# Chargement des variables d’environnement depuis le fichier .env
from dotenv import load_dotenv

# Fenêtre principale de l’application (navigation + pages)
from crimevision.core.db.database import init_db, close_db

# Fenêtre principale de l’application (navigation + pages)
from crimevision.ui.views.main_window import MainWindow

# Page de connexion affichée au démarrage
from crimevision.ui.views.login_page import LoginPage

# Gestionnaire de thème visuel (QSS)
from crimevision.ui.theme.theme_manager import apply_theme


# Chemin vers le dossier des ressources graphiques
ASSETS = Path(__file__).parent / "assets"

# Point d’entrée principal de l’application
def main():

    # Chargement des variables d’environnement (.env)
    load_dotenv()

    # Initialisation de la connexion à la base de données
    init_db()

    # Création de l’application Qt avec les arguments système
    app = QApplication(sys.argv)

    # Définition du style graphique global Qt
    app.setStyle("Fusion")

    # Autorise la propagation des styles QSS dans les widgets enfants
    app.setAttribute(Qt.AA_UseStyleSheetPropagationInWidgetStyles, True)

    # Indique à l’application l’utilisation d’un thème sombre sous Windows
    app.setProperty("windowsDarkMode", True)

    # Chargement et application de l’icône de l’application si disponible
    icon_path = ASSETS / "crimevision_eye.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Application du thème visuel principal (dark.qss)
    apply_theme(app, "dark")

    # Création de la fenêtre principale de l’application
    win = MainWindow()
    login = LoginPage(ASSETS)
    win.set_login_page(login)
    win.show_login()
    win.show()

    # Lancement de la boucle principale Qt
    code = app.exec()

    # Fermeture propre de la connexion à la base de données
    close_db()
    sys.exit(code)

# Permet d’exécuter le programme uniquement s’il est lancé directement
if __name__ == "__main__":
    main()
