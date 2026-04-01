from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from backend.auth_operations import authenticate_user


class LoginTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent  # Reference to MainWindow for updating user state
        self.current_user = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # User Info (shown if logged in)
        self.user_info_label = QLabel("Not logged in")
        self.user_info_label.setStyleSheet("background-color: #e0e0e0; padding: 5px;")
        layout.addWidget(self.user_info_label)

        # Username
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("Username:"))
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Enter username")
        username_layout.addWidget(self.login_username)
        layout.addLayout(username_layout)

        # Password
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("Password:"))
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Enter password")
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(self.login_password)
        layout.addLayout(password_layout)

        # Buttons
        buttons_layout = QHBoxLayout()
        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.on_login)
        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self.on_logout)
        buttons_layout.addWidget(login_btn)
        buttons_layout.addWidget(logout_btn)
        layout.addLayout(buttons_layout)

        # Note
        note = QLabel("Note: New users must be created by an admin from the User Management tab.")
        note.setWordWrap(True)
        layout.addWidget(note)

        layout.addStretch()
        self.setLayout(layout)

    def on_login(self):
        username = self.login_username.text().strip()
        password = self.login_password.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter both username and password")
            return

        user = authenticate_user(username, password)
        if user:
            self.current_user = user
            self.user_info_label.setText(
                f"Logged in as: {user.get('full_name', 'Unknown')} ({user.get('role', 'user')})"
            )
            self.login_username.clear()
            self.login_password.clear()
            # Update MainWindow's user state
            self.main_window.current_user = user
            self.main_window.update_ui_for_user()
            QMessageBox.information(self, "Success", "Login successful")
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password")

    def on_logout(self):
        if not self.current_user:
            QMessageBox.warning(self, "Error", "No user is currently logged in")
            return
        self.current_user = None
        self.user_info_label.setText("Not logged in")
        self.main_window.current_user = None
        self.main_window.update_ui_for_user()
        QMessageBox.information(self, "Success", "Logged out successfully")

    def update_user_info(self):
        if self.current_user:
            self.user_info_label.setText(
                f"Logged in as: {self.current_user.get('full_name', 'Unknown')} ({self.current_user.get('role', 'user')})"
            )
        else:
            self.user_info_label.setText("Not logged in")