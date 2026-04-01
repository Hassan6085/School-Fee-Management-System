from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QComboBox, QMessageBox, QFormLayout, QGroupBox
)
from PyQt6.QtCore import Qt
import os
from backend.auth_operations import get_all_users, delete_user_admin, update_user_role_admin, register_user


class UserManagementTab(QWidget):
    def __init__(self, current_user, emitter=None):
        super().__init__()
        self.current_user = current_user
        self.emitter = emitter
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # --- 1. Users Table ---
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(6)
        self.users_table.setHorizontalHeaderLabels(['ID', 'Username', 'Full Name', 'Email', 'Role', 'Created At'])
        self.users_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        # Select full rows for easier deletion/editing
        self.users_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.users_table)

        # --- 2. Action Controls (Role Change & Delete) ---
        action_group = QGroupBox("Manage Selected User")
        action_layout = QHBoxLayout()

        self.user_role_combo = QComboBox()
        self.user_role_combo.addItems(['user', 'admin'])

        change_role_btn = QPushButton('Update Role')
        change_role_btn.clicked.connect(self.on_change_user_role)

        delete_user_btn = QPushButton('Delete User')
        delete_user_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        delete_user_btn.clicked.connect(self.on_delete_user)

        action_layout.addWidget(QLabel("New Role:"))
        action_layout.addWidget(self.user_role_combo)
        action_layout.addWidget(change_role_btn)
        action_layout.addStretch()
        action_layout.addWidget(delete_user_btn)

        action_group.setLayout(action_layout)
        layout.addWidget(action_group)

        # --- 3. Add New User Form ---
        add_user_group = QGroupBox("Add New User")
        add_user_layout = QFormLayout()

        self.new_username = QLineEdit()
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_full_name = QLineEdit()
        self.new_email = QLineEdit()
        self.new_role = QComboBox()
        self.new_role.addItems(['user', 'admin'])

        add_user_btn = QPushButton("Create User")
        add_user_btn.clicked.connect(self.on_add_user)

        add_user_layout.addRow("Username:", self.new_username)
        add_user_layout.addRow("Password:", self.new_password)
        add_user_layout.addRow("Full Name:", self.new_full_name)
        add_user_layout.addRow("Email:", self.new_email)
        add_user_layout.addRow("Role:", self.new_role)
        add_user_layout.addRow(add_user_btn)

        add_user_group.setLayout(add_user_layout)
        layout.addWidget(add_user_group)

        self.setLayout(layout)

        # Initial Load
        self.load_users_table()

        # Connect to emitter for updates (if another admin adds a user)
        if self.emitter:
            self.emitter.data_changed.connect(self.reload_data)

        # Load stylesheet
        try:
            with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ui', 'styles.css'), 'r') as f:
                self.setStyleSheet(f.read())
        except:
            pass

    def reload_data(self):
        self.load_users_table()

    def load_users_table(self):
        try:
            users = get_all_users()
            self.users_table.setRowCount(len(users))
            for i, user in enumerate(users):
                # user tuple: (id, username, full_name, email, role, created_at)
                for j, val in enumerate(user):
                    self.users_table.setItem(i, j, QTableWidgetItem(str(val) if val is not None else ''))
        except Exception as e:
            print(f"Error loading users: {e}")

    def on_add_user(self):
        if not self.current_user or self.current_user.get('role') != 'admin':
            QMessageBox.warning(self, "Error", "Admin privileges required")
            return

        username = self.new_username.text().strip()
        password = self.new_password.text().strip()
        full_name = self.new_full_name.text().strip()
        email = self.new_email.text().strip()
        role = self.new_role.currentText()

        if not all([username, password, full_name, email]):
            QMessageBox.warning(self, "Error", "Please fill all required fields")
            return

        try:
            if register_user(username, password, full_name, email, role):
                QMessageBox.information(self, "Success", f"User '{username}' added successfully")
                self.load_users_table()
                self.new_username.clear()
                self.new_password.clear()
                self.new_full_name.clear()
                self.new_email.clear()
                self.new_role.setCurrentIndex(0)
                if self.emitter:
                    self.emitter.data_changed.emit()
            else:
                QMessageBox.warning(self, "Error", "Username already exists or database error")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to add user: {str(e)}")

    def on_change_user_role(self):
        if not self.current_user or self.current_user.get('role') != 'admin':
            QMessageBox.warning(self, "Error", "Admin privileges required")
            return

        selected_row = self.users_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Error", "Please select a user first")
            return

        user_id = int(self.users_table.item(selected_row, 0).text())
        new_role = self.user_role_combo.currentText()

        # Prevent admin from removing their own admin status accidentally
        if user_id == self.current_user.get('id'):
            QMessageBox.warning(self, "Warning", "You cannot change your own role.")
            return

        try:
            update_user_role_admin(self.current_user['id'], user_id, new_role)
            QMessageBox.information(self, "Success", f"User role updated to {new_role}")
            self.load_users_table()
            if self.emitter:
                self.emitter.data_changed.emit()
        except PermissionError:
            QMessageBox.warning(self, "Error", "Permission Denied")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def on_delete_user(self):
        if not self.current_user or self.current_user.get('role') != 'admin':
            QMessageBox.warning(self, "Error", "Admin privileges required")
            return

        selected_row = self.users_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Error", "Please select a user first")
            return

        user_id = int(self.users_table.item(selected_row, 0).text())
        username = self.users_table.item(selected_row, 1).text()

        # Prevent admin from deleting themselves
        if user_id == self.current_user.get('id'):
            QMessageBox.warning(self, "Warning", "You cannot delete your own account.")
            return

        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete user '{username}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                delete_user_admin(self.current_user['id'], user_id)
                QMessageBox.information(self, "Success", "User deleted successfully")
                self.load_users_table()
                if self.emitter:
                    self.emitter.data_changed.emit()
            except PermissionError:
                QMessageBox.warning(self, "Error", "Permission Denied")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))