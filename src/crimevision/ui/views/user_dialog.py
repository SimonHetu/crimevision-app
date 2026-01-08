from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QLabel, QMessageBox
)

# Boîte de dialogue utilisée pour créer ou modifier un utilisateur
class UserDialog(QDialog):

    # Initialise la fenêtre de dialogue en mode ajout ou édition
    def __init__(
        self,
        *,
        title: str,
        email: str = "",
        name: str = "",
        pseudo: str = "",
        edit_mode: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self._edit_mode = edit_mode

        # Layout principal de la fenêtre de dialogue
        root = QVBoxLayout(self)

        # Zone d’information contextuelle (instructions selon le mode)
        self.info = QLabel()
        root.addWidget(self.info)

        # Formulaire contenant les champs utilisateur
        form = QFormLayout()
        root.addLayout(form)

        # Champs de saisie (email, nom, pseudo)
        self.email_in = QLineEdit(email)
        self.name_in = QLineEdit(name)
        self.pseudo_in = QLineEdit(pseudo)

        # Champ de saisie du mot de passe
        self.password_in = QLineEdit()
        self.password_in.setEchoMode(QLineEdit.Password)

        # Champ de confirmation du mot de passe (édition seulement)
        self.confirm_in = QLineEdit()
        self.confirm_in.setEchoMode(QLineEdit.Password)

        form.addRow("Email", self.email_in)
        form.addRow("Name", self.name_in)
        form.addRow("Pseudo", self.pseudo_in)

        # Configuration du formulaire selon le mode (ajout ou édition)
        if edit_mode:
            self.info.setText("Nouveau mot de passe optionnel laisser vide garder le même")
            self.password_in.setPlaceholderText("Laisser vide pour garder le même mot de passe")
            self.confirm_in.setPlaceholderText("Confirmer le nouveau mot de passe")

            form.addRow("New Password", self.password_in)
            form.addRow("Confirm Password", self.confirm_in)
        else:
            self.info.setText("Mot de passe requis pour créer un nouvel utilisateur")
            self.password_in.setPlaceholderText("Requis")

            form.addRow("Password", self.password_in)

        # Boutons de validation et d’annulation
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self._on_ok)
        self.buttons.rejected.connect(self.reject)
        root.addWidget(self.buttons)

    # Validation des champs avant d’accepter le formulaire
    def _on_ok(self):
        email = self.email_in.text().strip()
        name = self.name_in.text().strip()
        pseudo = self.pseudo_in.text().strip()
        password = self.password_in.text()

        if not email or not name or not pseudo:
            QMessageBox.warning(self, "Validation", "Email, Name et Pseudo requis")
            return

        if not self._edit_mode and not password:
            QMessageBox.warning(self, "Validation", "Mot de passe requis")
            return

        if self._edit_mode and password:
            if password != self.confirm_in.text():
                QMessageBox.warning(self, "Validation", "Mots de passe non identique")
                return

        self.accept()

    # Retourne les valeurs saisies pour traitement par la page appelante
    def values(self):
        return (
            self.email_in.text().strip(),
            self.name_in.text().strip(),
            self.pseudo_in.text().strip(),
            self.password_in.text(),
        )
