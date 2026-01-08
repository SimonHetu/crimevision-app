# Outils Qt pour interactions
from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QPushButton, QMessageBox, QMenu, QDialog
)

# Utilisé pour convertir/afficher les dates au format local
from datetime import datetime, timezone

# Service responsable des opérations DB liées aux utilisateurs (CRUD)
from crimevision.core.services.user_service import UserService

# Boîte de dialogue UI utilisée pour ajouter/modifier un utilisateur
from crimevision.ui.views.user_dialog import UserDialog


# Page d’administration qui permet de consulter et gérer les utilisateurs (CRUD complet)
class UsersPage(QWidget):
    def __init__(self):
        super().__init__()
        self.service = UserService()

        # Layout principal de la page (titre + table + boutons)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Users"))

        # Table principale qui affiche les colonnes de la table User (ID, email, etc.)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Email", "Name", "Pseudo", "Created", "Updated"])

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        # Rangée de boutons pour exécuter les actions admin (refresh, add, edit, delete)
        btn_row = QHBoxLayout()
        self.btn_refresh = QPushButton("Refresh")
        self.btn_add = QPushButton("Add")
        self.btn_edit = QPushButton("Edit")
        self.btn_delete = QPushButton("Delete")

        btn_row.addWidget(self.btn_refresh)
        btn_row.addWidget(self.btn_add)
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_edit)
        btn_row.addWidget(self.btn_delete)
        layout.addLayout(btn_row)

        # Connexions des boutons aux fonctions de gestion (CRUD)
        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_add.clicked.connect(self.add_user)
        self.btn_edit.clicked.connect(self.edit_selected_user)
        self.btn_delete.clicked.connect(self.delete_selected_user)

        # Menu contextuel (clic droit) pour déclencher les mêmes actions rapidement
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        # Double-clic sur une ligne = ouverture directe de la fenêtre d’édition
        self.table.itemDoubleClicked.connect(lambda _: self.edit_selected_user())

        # Chargement initial des données
        self.refresh()

    # Récupère l’ID de l’utilisateur sélectionné dans la table (ou None si rien n’est sélectionné)
    def _selected_user_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if not item:
            return None
        return item.data(Qt.UserRole)
    

    # Formate une date de la DB en heure locale lisible
    def fmt_local(self, dt):
        if not dt:
            return ""
       
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone().strftime("%Y-%m-%d %H:%M")

    # Recharge la liste d’utilisateurs depuis la DB et remplit la table UI
    def refresh(self):
        try:
            users = self.service.list_users(limit=50)
        except Exception as e:
            QMessageBox.critical(self, "DB Error", str(e))
            return

        self.table.setRowCount(len(users))
        for row, u in enumerate(users):
            user_id = int(u["id"])

            id_item = QTableWidgetItem(str(user_id))
            id_item.setData(Qt.UserRole, user_id)
            self.table.setItem(row, 0, id_item)

            self.table.setItem(row, 1, QTableWidgetItem(u.get("email", "")))
            self.table.setItem(row, 2, QTableWidgetItem(u.get("name", "")))
            self.table.setItem(row, 3, QTableWidgetItem(u.get("pseudo", "")))

            self.table.setItem(row, 4, QTableWidgetItem(self.fmt_local(u.get("createdAt"))))
            self.table.setItem(row, 5, QTableWidgetItem(self.fmt_local(u.get("updatedAt"))))

        self.table.resizeColumnsToContents()

    # Affiche un menu contextuel permettant d’exécuter les actions CRUD sur la sélection
    def show_context_menu(self, pos: QPoint):
        menu = QMenu(self)

        act_refresh = menu.addAction("Refresh")
        menu.addSeparator()
        act_add = menu.addAction("Add user…")
        act_edit = menu.addAction("Edit selected…")
        act_del = menu.addAction("Delete selected…")

        has_sel = self._selected_user_id() is not None
        act_edit.setEnabled(has_sel)
        act_del.setEnabled(has_sel)

        chosen = menu.exec(self.table.viewport().mapToGlobal(pos))
        if chosen == act_refresh:
            self.refresh()
        elif chosen == act_add:
            self.add_user()
        elif chosen == act_edit:
            self.edit_selected_user()
        elif chosen == act_del:
            self.delete_selected_user()

    # Ouvre une fenêtre pour créer un nouvel utilisateur, valide les champs, puis enregistre en DB
    def add_user(self):
        dlg = UserDialog(title="Add user", edit_mode=False, parent=self)
        if dlg.exec() != QDialog.Accepted:
            return


        email, name, pseudo, password = dlg.values()

        if not email or not name or not pseudo or not password:
            QMessageBox.warning(self, "Validation", "Email, Name, et Password requis.")
            return

        try:
            self.service.create_user(email=email, name=name, pseudo=pseudo, password=password)
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Add failed", str(e))

    # Ouvre une fenêtre pour modifier l’utilisateur sélectionné et applique les changements en DB
    def edit_selected_user(self):
        user_id = self._selected_user_id()
        if user_id is None:
            QMessageBox.information(self, "Edit", "Select a user first.")
            return

        row = self.table.currentRow()
        current_email = self.table.item(row, 1).text()
        current_name = self.table.item(row, 2).text()
        current_pseudo = self.table.item(row, 3).text()

        dlg = UserDialog(
            title=f"Edit user #{user_id}",
            email=current_email,
            name=current_name,
            pseudo=current_pseudo,
            edit_mode=True,
            parent=self,
        )

        if dlg.exec() != QDialog.Accepted:
            return

        email, name, pseudo, password = dlg.values()

        if not email or not name or not pseudo:
            QMessageBox.warning(self, "Validation", "Email, Name and Pseudo are required.")
            return

        try:
            self.service.update_user(
            user_id,
            email=email,
            name=name,
            pseudo=pseudo,
            password=password or None,
        )
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Edit failed", str(e))


    # Supprime l’utilisateur sélectionné après confirmation et met à jour l’interface
    def delete_selected_user(self):
        user_id = self._selected_user_id()
        if user_id is None:
            QMessageBox.information(self, "Delete", "Select a user first.")
            return

        confirm = QMessageBox.question(
            self,
            "Delete user",
            f"Delete user #{user_id}? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            self.service.delete_user(user_id)
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Delete failed", str(e))
