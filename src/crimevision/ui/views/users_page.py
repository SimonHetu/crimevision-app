# users_page.py
from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QPushButton, QMessageBox, QMenu, QDialog
)

from datetime import timezone

from crimevision.core.services.user_service import UserService
from crimevision.ui.views.user_dialog import UserDialog


class UsersPage(QWidget):
    def __init__(self):
        super().__init__()
        self.service = UserService()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Users"))

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Email", "Role", "Created", "Updated"])

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

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

        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_add.clicked.connect(self.add_user)
        self.btn_edit.clicked.connect(self.edit_selected_user)
        self.btn_delete.clicked.connect(self.delete_selected_user)

        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        self.table.itemDoubleClicked.connect(lambda _: self.edit_selected_user())

        self.refresh()

    def _selected_user_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if not item:
            return None
        return item.data(Qt.UserRole)


    def fmt_local(self, dt):
        if not dt:
            return ""
        # Assume UTC if naive
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone().strftime("%Y-%m-%d %H:%M")

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
            self.table.setItem(row, 2, QTableWidgetItem(u.get("role", "")))
            self.table.setItem(row, 3, QTableWidgetItem(self.fmt_local(u.get("createdAt"))))
            self.table.setItem(row, 4, QTableWidgetItem(self.fmt_local(u.get("updatedAt"))))

        self.table.resizeColumnsToContents()

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

    def add_user(self):
        dlg = UserDialog(title="Add user", edit_mode=False, parent=self)
        if dlg.exec() != QDialog.Accepted:
            return

        (email,) = dlg.values()

        try:
            self.service.create_user(email=email)
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Add failed", str(e))

    def edit_selected_user(self):
        user_id = self._selected_user_id()
        if user_id is None:
            QMessageBox.information(self, "Edit", "Select a user first.")
            return

        row = self.table.currentRow()
        current_email = self.table.item(row, 1).text()

        dlg = UserDialog(
            title=f"Edit user #{user_id}",
            email=current_email,
            edit_mode=True,
            parent=self,
        )

        if dlg.exec() != QDialog.Accepted:
            return

        (email,) = dlg.values()

        try:
            self.service.update_user(user_id, email=email)
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Edit failed", str(e))

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