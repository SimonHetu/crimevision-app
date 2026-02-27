from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QIcon, QAction
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


# =========================================================
# LOGIN PAGE — CrimeVision
# ---------------------------------------------------------
# Rôle :
# - Page de connexion affichée au démarrage
# - Watermark (grand logo) en arrière-plan
# - Carte au centre avec champs + bouton
# - Émet un signal loginRequested(user, pwd)
# =========================================================
class LoginPage(QWidget):
    # Signal émis lorsque l’utilisateur soumet ses identifiants
    loginRequested = Signal(str, str)

    def __init__(self, assets_dir: Path):
        super().__init__()
        self.assets_dir = assets_dir

        # -------------------------
        # Layout racine
        # -------------------------
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # -------------------------
        # Background (watermark)
        # -------------------------
        bg = QFrame()
        bg.setObjectName("loginBg")
        bg_layout = QVBoxLayout(bg)
        bg_layout.setContentsMargins(0, 0, 0, 0)
        bg_layout.setSpacing(0)

        self.watermark = QLabel()
        self.watermark.setObjectName("loginWatermark")
        self.watermark.setAlignment(Qt.AlignCenter)
        self.watermark.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.watermark.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        bg_layout.addWidget(self.watermark, 1)

        # -------------------------
        # Foreground (contenu)
        # -------------------------
        fg = QWidget()
        fg.setObjectName("loginFg")
        fg_layout = QVBoxLayout(fg)
        fg_layout.setContentsMargins(24, 24, 24, 24)
        fg_layout.setSpacing(14)
        fg_layout.addStretch()

        # -------------------------
        # Carte centrale
        # -------------------------
        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedWidth(420)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(12)

        # En-tête : seulement le titre (plus minimal)
        title = QLabel("CrimeVision")
        title.setObjectName("loginTitle")
        card_layout.addWidget(title)

        # Sous-titre
        subtitle = QLabel("Console d’administration")
        subtitle.setObjectName("loginSubtitle")
        card_layout.addWidget(subtitle)

        # -------------------------
        # Champs
        # -------------------------
        self.username = QLineEdit()
        self.username.setObjectName("loginInput")
        self.username.setPlaceholderText("Email ou nom d’utilisateur")

        self.password = QLineEdit()
        self.password.setObjectName("loginInput")
        self.password.setPlaceholderText("Mot de passe")
        self.password.setEchoMode(QLineEdit.Password)

        # --- Eye toggle (show/hide password) ---
        self._pwd_visible = False

        eye_open_path = self.assets_dir / "eye.svg"
        eye_closed_path = self.assets_dir / "eye-off.svg"

        self._eye_open_icon = QIcon(str(eye_open_path)) if eye_open_path.exists() else QIcon()
        self._eye_closed_icon = QIcon(str(eye_closed_path)) if eye_closed_path.exists() else QIcon()

        self._toggle_pwd_action = QAction(self.password)
        self._toggle_pwd_action.setCheckable(True)
        self._toggle_pwd_action.setToolTip("Afficher / masquer le mot de passe")

        # icon initial
        if not self._eye_closed_icon.isNull():
            self._toggle_pwd_action.setIcon(self._eye_closed_icon)
        else:
            self._toggle_pwd_action.setText("👁")

        # place it inside the line edit
        self.password.addAction(self._toggle_pwd_action, QLineEdit.TrailingPosition)
        self._toggle_pwd_action.toggled.connect(self._toggle_password_visibility)

        card_layout.addWidget(self.username)
        card_layout.addWidget(self.password)

        # -------------------------
        # Bouton
        # -------------------------
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.login_btn = QPushButton("Connexion")
        self.login_btn.setObjectName("loginButton")
        self.login_btn.clicked.connect(self._emit_login)

        btn_row.addWidget(self.login_btn)
        card_layout.addLayout(btn_row)

        fg_layout.addWidget(card, 0, Qt.AlignHCenter)

        # Petit texte d’aide
        self.help_text = QLabel("")
        self.help_text.setObjectName("loginHelp")
        fg_layout.addWidget(self.help_text, 0, Qt.AlignHCenter)

        fg_layout.addStretch()

        # -------------------------
        # Assemblage
        # -------------------------
        root.addWidget(bg)
        root.addWidget(fg, 0, Qt.AlignCenter)

        # UX : Enter sur username -> focus password, Enter sur password -> login
        self.username.returnPressed.connect(self.password.setFocus)
        self.password.returnPressed.connect(self._emit_login)

        # Focus initial
        self.username.setFocus()

        # Chargement images + styles
        self._load_logos()
        self._apply_login_styles()

    # =========================================================
    # Chargement du logo principal (watermark)
    # =========================================================
    def _load_logos(self):
        logo_path = self.assets_dir / "crimevision_logo_10.png"
        if logo_path.exists():
            pix = QPixmap(str(logo_path))
            if not pix.isNull():
                big = pix.scaledToWidth(520, Qt.SmoothTransformation)
                self.watermark.setPixmap(big)
                return
        self.watermark.setText("")

    # =========================================================
    # Styles (QSS)
    # =========================================================
    def _apply_login_styles(self):
        self.setStyleSheet("""
        #loginFg { background: transparent; }

        #loginCard {
            background-color: #0b1220;
            border: 1px solid #334155;
            border-radius: 10px;
        }

        #loginTitle {
            color: #f8fafc;
            font-size: 22px;
            font-weight: 800;
        }

        #loginSubtitle {
            color: #94a3b8;
            font-size: 12px;
            margin-bottom: 6px;
        }

        #loginInput {
            background-color: #0f172a;
            color: #f8fafc;
            padding: 10px 34px 10px 12px; /* right padding for the eye */
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

    # =========================================================
    # Émet le signal de connexion vers la fenêtre principale
    # =========================================================
    def _emit_login(self):
        user = self.username.text().strip()
        pwd = self.password.text()
        self.loginRequested.emit(user, pwd)

    def set_error(self, msg: str):
        self.help_text.setText(msg)

    def _toggle_password_visibility(self, checked: bool):
        self._pwd_visible = checked
        self.password.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)

        # keep cursor at end
        self.password.setCursorPosition(len(self.password.text()))

        # swap icon
        if checked and not self._eye_open_icon.isNull():
            self._toggle_pwd_action.setIcon(self._eye_open_icon)
        elif (not checked) and not self._eye_closed_icon.isNull():
            self._toggle_pwd_action.setIcon(self._eye_closed_icon)