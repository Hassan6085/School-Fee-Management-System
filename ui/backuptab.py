from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox, QComboBox, QLineEdit
from backend.backup_operations import backup_database, authenticate_drive, restore_database
import os
from backend.data_emitter import DataEmitter  # New import

class BackupTab(QWidget):
    def __init__(self, current_user, emitter=None):  # Updated to accept emitter
        super().__init__()
        self.current_user = current_user
        self.emitter = emitter  # Store emitter for signal emission and connection
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Dropdown Actions
        self.action_combo = QComboBox()
        self.action_combo.addItems(['Select Action', 'Connect to Google Drive', 'Backup to Google Drive', 'Restore Latest Backup'])
        self.action_combo.currentIndexChanged.connect(self.on_action_changed)
        layout.addWidget(self.action_combo)

        # Info
        layout.addWidget(QLabel(""))

        self.setLayout(layout)

        # Connect to emitter for real-time updates
        if self.emitter:
            self.emitter.data_changed.connect(self.reload_data)

        # Style
        with open(os.path.join(os.path.dirname(__file__), 'styles.css'), 'r') as f:
            self.setStyleSheet(f.read())

    def on_action_changed(self, index):
        action = self.action_combo.currentText()
        if action == 'Connect to Google Drive':
            self.on_connect_drive()
        elif action == 'Backup to Google Drive':
            self.on_backup()
        elif action == 'Restore Latest Backup':
            self.on_restore()

    def on_connect_drive(self):
        try:
            authenticate_drive()
            QMessageBox.information(self, "Connected", "Google Drive connected successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to connect: {str(e)}")

    def on_backup(self):
        try:
            result = backup_database(self.current_user)
            QMessageBox.information(
                self,
                "Success",
                f"Backup uploaded.\nLatest ID: {result['latest']}\nHistory ID: {result['history']}"
            )
            if self.emitter:
                self.emitter.data_changed.emit()  # Emit signal to update other tabs after backup
        except Exception as e:
            QMessageBox.warning(self, "Backup Error", str(e))

    def on_restore(self):
        try:
            restore_database()
            QMessageBox.information(self, "Success", "Database restored from latest backup.")
            if self.emitter:
                self.emitter.data_changed.emit()  # Emit signal to update other tabs after restore
        except Exception as e:
            QMessageBox.warning(self, "Restore Error", str(e))

    def reload_data(self):
        """Reload the tab data if needed (placeholder for future expansion)."""
        pass  # Currently no dynamic data to reload, but kept for consistency