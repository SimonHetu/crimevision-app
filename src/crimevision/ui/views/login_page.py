from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QSizePolicy,
)

# Page de connexion affichée au démarrage de l’application
class LoginPage(QWidget):
    
    # Signal émis lorsque l’utilisateur soumet ses identifiants
    loginRequested = Signal(str, str)
    

    # Initialisation de l’interface de login
    def __init__(self, assets_dir: Path):
        super().__init__()
        self.assets_dir = assets_dir

        # Layout racine de la page
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Conteneur d’arrière-plan (watermark / style global)
        bg = QFrame()
        bg.setObjectName("loginBg")
        bg_layout = QVBoxLayout(bg)
        bg_layout.setContentsMargins(0, 0, 0, 0)
        bg_layout.setSpacing(0)

        # Logo affiché en arrière-plan
        self.watermark = QLabel()
        self.watermark.setObjectName("loginWatermark")
        self.watermark.setAlignment(Qt.AlignCenter)
        self.watermark.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.watermark.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        bg_layout.addWidget(self.watermark, 1)

        # Conteneur de premier plan (contenu interactif)
        fg = QWidget()
        fg.setObjectName("loginFg")
        fg_layout = QVBoxLayout(fg)
        fg_layout.setContentsMargins(24, 24, 24, 24)
        fg_layout.setSpacing(14)
        fg_layout.addStretch()

        # Carte centrale contenant le formulaire de connexion
        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedWidth(420)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(12)

        # En-tête de la carte (logo + titre)
        header = QHBoxLayout()
        header.setSpacing(12)

        self.logo_small = QLabel()
        self.logo_small.setObjectName("loginLogoSmall")
        self.logo_small.setFixedSize(40, 40)
        self.logo_small.setScaledContents(True)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("CrimeVision")
        title.setObjectName("loginTitle")
        subtitle = QLabel("Admin access")
        subtitle.setObjectName("loginSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)

        header.addWidget(self.logo_small)
        header.addLayout(title_col)
        header.addStretch()
        card_layout.addLayout(header)

        # Champs de saisie utilisateur (identifiant et mot de passe)
        self.username = QLineEdit()
        self.username.setObjectName("loginInput")
        self.username.setPlaceholderText("Email or username")

        self.password = QLineEdit()
        self.password.setObjectName("loginInput")
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)

        card_layout.addWidget(self.username)
        card_layout.addWidget(self.password)

        # Zone d’action contenant le bouton de connexion
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.login_btn = QPushButton("Login")
        self.login_btn.setObjectName("loginButton")
        self.login_btn.clicked.connect(self._emit_login)
        btn_row.addWidget(self.login_btn)
        card_layout.addLayout(btn_row)

        fg_layout.addWidget(card, 0, Qt.AlignHCenter)

        # Texte d’aide informatif sous la carte
        help_text = QLabel("Pour l'instant tout mot de passe et identifiant fonctionne")
        help_text.setObjectName("loginHelp")
        fg_layout.addWidget(help_text, 0, Qt.AlignHCenter)
        fg_layout.addStretch()

        # Assemblage final des couches background / foreground
        root.addWidget(bg)
        root.addWidget(fg, 0, Qt.AlignCenter)

        # Validation du login avec la touche Entrée
        self.password.returnPressed.connect(self._emit_login)

        # Chargement des logos depuis les assets
        self._load_logos()

        # Application des styles spécifiques à la page de login
        self._apply_login_styles()


    # Chargement du logo principal et du watermark
    def _load_logos(self):
        logo_path = self.assets_dir / "crimevision_logo_10.png"
        if logo_path.exists():
            pix = QPixmap(str(logo_path))
            if not pix.isNull():
                self.logo_small.setPixmap(pix)
                big = pix.scaledToWidth(520, Qt.SmoothTransformation)
                self.watermark.setPixmap(big)
                return
        self.logo_small.setText("🧿")
        self.watermark.setText("")

    # Application du style visuel (QSS) propre à la page de login
    def _apply_login_styles(self):
        self.setStyleSheet("""
        /* Let your global QWidget theme handle the background */
        #loginFg { background: transparent; }

        #loginCard {
            background-color: #0b1220;
            border: 1px solid #334155;
            border-radius: 10px;
        }

        #loginTitle {
            color: #f8fafc;
            font-size: 20px;
            font-weight: 700;
        }

        #loginSubtitle {
            color: #94a3b8;
            font-size: 12px;
        }

        #loginInput {
            background-color: #0f172a;
            color: #f8fafc;
            padding: 10px 12px;
            border: 1px solid #334155;
            border-radius: 8px;
        }

        #loginInput:focus {
            border: 1px solid #1e40af;
        }

        #loginButton {
            background-color: #1e40af;
            color: #f8fafc;
            padding: 10px 16px;
            border-radius: 8px;
            font-weight: 700;
        }

        #loginButton:hover {
            background-color: #2b53cf;
        }

        #loginHelp {
            color: #94a3b8;
            font-size: 11px;
        }
        """)

    # Émet le signal de connexion vers la fenêtre principale
    def _emit_login(self):
        user = self.username.text().strip()
        pwd = self.password.text()
        self.loginRequested.emit(user, pwd)
