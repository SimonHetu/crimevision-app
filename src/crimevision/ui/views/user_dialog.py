from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QLabel, QMessageBox
)

class UserDialog(QDialog):
    """
    Dialogue pour créer / modifier un utilisateur.
    Compatible avec Clerk: pas de password, pas de pseudo, etc.
    """

    def __init__(
        self,
        *,
        title: str,
        email: str = "",
        edit_mode: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self._edit_mode = edit_mode

        root = QVBoxLayout(self)

        self.info = QLabel()
        self.info.setText(
            "Créer un utilisateur (auth gérée par Clerk)." if not edit_mode
            else "Modifier l'utilisateur."
        )
        root.addWidget(self.info)

        form = QFormLayout()
        root.addLayout(form)

        self.email_in = QLineEdit(email)
        self.email_in.setPlaceholderText("email@example.com")
        form.addRow("Email", self.email_in)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self._on_ok)
        self.buttons.rejected.connect(self.reject)
        root.addWidget(self.buttons)

    def _on_ok(self):
        email = self.email_in.text().strip()

        if not email:
            QMessageBox.warning(self, "Validation", "Email requis.")
            return
        if "@" not in email:
            QMessageBox.warning(self, "Validation", "Email invalide.")
            return

        self.accept()

    def values(self):
        return (self.email_in.text().strip(),)