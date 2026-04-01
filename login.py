from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QWidget, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from backend.auth_operations import authenticate_user
import os


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("School Fee Manager - Login")
        self.setModal(True)
        self.resize(420, 420)
        self.user_data = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(18)

        # ===== Logo =====
        logo_path = r"ui\logo.png"
        if os.path.exists(logo_path):
            logo_label = QLabel()
            pixmap = QPixmap(logo_path)
            pixmap = pixmap.scaled(100, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(logo_label)

        # ===== Title =====
        title = QLabel("Usman's Kindergarten High School Sargodha School Fee Manager")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Login to continue")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # Spacer
        layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # ===== Username =====
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Enter username")
        self.login_username.setFixedHeight(36)
        self.login_username.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.login_username)

        # ===== Password =====
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Enter password")
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_password.setFixedHeight(36)
        self.login_password.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.login_password.returnPressed.connect(self.login)
        layout.addWidget(self.login_password)

        # ===== Buttons =====
        btn_layout = QHBoxLayout()
        login_btn = QPushButton("Login")
        login_btn.setDefault(True)
        login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        login_btn.clicked.connect(self.login)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(login_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        # ===== Note =====
        note = QLabel("Note: New users must be created by an admin from the application.")
        note.setWordWrap(True)
        note.setObjectName("noteLabel")
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(note)

        self.setLayout(layout)

        # ===== Styling =====
        self.setStyleSheet("""
            QDialog {
                background-color: #1b1f2f;
                border-radius: 10px;
            }
            #titleLabel {
                font-size: 22px;
                font-weight: bold;
                color: #f1c40f;
            }
            #subtitleLabel {
                font-size: 13px;
                color: #bbbbbb;
                margin-bottom: 8px;
            }
            QLineEdit {
                border: 2px solid #2e3a59;
                border-radius: 6px;
                padding: 6px;
                font-size: 14px;
                color: #ffffff;
                background-color: #252b3b;
            }
            QLineEdit:focus {
                border: 2px solid #f1c40f;
                background-color: #2f3649;
            }
            QPushButton {
                background-color: #f1c40f;
                border: none;
                border-radius: 6px;
                padding: 8px 14px;
                color: #1b1f2f;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ffd633;
            }
            QPushButton:pressed {
                background-color: #c7a600;
            }
            #noteLabel {
                font-size: 12px;
                color: #cccccc;
                margin-top: 10px;
            }
        """)

        self.login_username.setFocus()

    def login(self):
        username = self.login_username.text().strip()
        password = self.login_password.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter both username and password")
            return

        user = authenticate_user(username, password)
        if user:
            self.user_data = user
            self.accept()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password")

    def get_credentials(self):
        return self.user_data if hasattr(self, 'user_data') else None
