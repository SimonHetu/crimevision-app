from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QLabel, QMessageBox
)

class UserDialog(QDialog):
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

        root = QVBoxLayout(self)

        self.info = QLabel()
        root.addWidget(self.info)

        form = QFormLayout()
        root.addLayout(form)

        self.email_in = QLineEdit(email)
        self.name_in = QLineEdit(name)
        self.pseudo_in = QLineEdit(pseudo)

        self.password_in = QLineEdit()
        self.password_in.setEchoMode(QLineEdit.Password)

        self.confirm_in = QLineEdit()
        self.confirm_in.setEchoMode(QLineEdit.Password)

        form.addRow("Email", self.email_in)
        form.addRow("Name", self.name_in)
        form.addRow("Pseudo", self.pseudo_in)

        if edit_mode:
            self.info.setText("New password is optional (leave blank to keep current password).")
            self.password_in.setPlaceholderText("Leave blank to keep current password")
            self.confirm_in.setPlaceholderText("Confirm new password")

            form.addRow("New Password", self.password_in)
            form.addRow("Confirm Password", self.confirm_in)
        else:
            self.info.setText("Password is required to create a user.")
            self.password_in.setPlaceholderText("Required")

            form.addRow("Password", self.password_in)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self._on_ok)
        self.buttons.rejected.connect(self.reject)
        root.addWidget(self.buttons)

    def _on_ok(self):
        email = self.email_in.text().strip()
        name = self.name_in.text().strip()
        pseudo = self.pseudo_in.text().strip()
        password = self.password_in.text()

        if not email or not name or not pseudo:
            QMessageBox.warning(self, "Validation", "Email, Name and Pseudo are required.")
            return

        if not self._edit_mode and not password:
            QMessageBox.warning(self, "Validation", "Password is required when adding a user.")
            return

        if self._edit_mode and password:
            if password != self.confirm_in.text():
                QMessageBox.warning(self, "Validation", "Passwords do not match.")
                return

        self.accept()

    def values(self):
        return (
            self.email_in.text().strip(),
            self.name_in.text().strip(),
            self.pseudo_in.text().strip(),
            self.password_in.text(),
        )
