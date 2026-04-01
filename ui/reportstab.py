from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit,
    QTableWidget, QTableWidgetItem, QMessageBox, QComboBox
)
import datetime

try:
    import pywhatkit
except ImportError:
    pywhatkit = None

from backend.fee_operations import get_defaulters
import os
from backend.data_emitter import DataEmitter  # New import

class ReportsTab(QWidget):
    def __init__(self, emitter=None):  # Updated to accept emitter
        super().__init__()
        self.emitter = emitter  # Store emitter for signal connection
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Filters Section (Placeholder for future expansion)
        filter_layout = QVBoxLayout()
        layout.addLayout(filter_layout)

        # Action Dropdown
        self.action_combo = QComboBox()
        self.action_combo.addItems(['Select Action', 'Show Defaulters', 'Send WhatsApp'])
        self.action_combo.currentIndexChanged.connect(self.on_action_changed)
        layout.addWidget(self.action_combo)

        # WhatsApp message input
        layout.addWidget(QLabel('WhatsApp Message (use {name} and {pending}):'))
        self.wh_msg = QTextEdit()
        layout.addWidget(self.wh_msg)

        # Defaulters Table
        self.def_table = QTableWidget()
        self.def_table.setColumnCount(7)
        self.def_table.setHorizontalHeaderLabels(['FeeID', 'Roll', 'Name', 'WhatsApp', 'Year', 'Month', 'Pending'])
        self.def_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.def_table)

        self.setLayout(layout)

        # Connect to emitter for real-time updates
        if self.emitter:
            self.emitter.data_changed.connect(self.reload_data)

        # Load existing stylesheet
        with open(os.path.join(os.path.dirname(__file__), 'styles.css'), 'r') as f:
            self.setStyleSheet(f.read())

    def on_action_changed(self, index):
        action = self.action_combo.currentText()
        if action == 'Show Defaulters':
            self.on_show_defaulters()
        elif action == 'Send WhatsApp':
            self.on_send_whatsapp()
        elif action == 'Select Action':
            pass  # Do nothing when default option is selected

    def on_show_defaulters(self):
        rows = get_defaulters()
        self.def_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for j, val in enumerate(r):
                self.def_table.setItem(i, j, QTableWidgetItem(str(val)))

    def on_send_whatsapp(self):
        if pywhatkit is None:
            QMessageBox.warning(self, 'Missing', 'pywhatkit not installed. Install with pip install pywhatkit')
            return

        selected = self.def_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, 'Error', 'Select at least one defaulter row')
            return

        rows = set(item.row() for item in selected)
        message = self.wh_msg.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, 'Empty', 'Type a message first')
            return

        now = datetime.datetime.now()
        minute_offset = 1  # Schedule each message 1 min apart

        for r in rows:
            wa = self.def_table.item(r, 3).text()
            pending = self.def_table.item(r, 6).text()
            name = self.def_table.item(r, 2).text()
            personalized = message.replace('{name}', name).replace('{pending}', pending)

            try:
                send_time = now + datetime.timedelta(minutes=minute_offset)
                h = send_time.hour
                m = send_time.minute
                pywhatkit.sendwhatmsg(wa, personalized, h, m, wait_time=10, tab_close=True)
                minute_offset += 1
            except Exception as e:
                QMessageBox.warning(self, 'WhatsApp Error', f'Error sending to {wa}: {e}')

        QMessageBox.information(self, 'Sent', 'WhatsApp messages scheduled/opened in browser')

    def reload_data(self):
        """Reload the defaulters table data."""
        self.on_show_defaulters()