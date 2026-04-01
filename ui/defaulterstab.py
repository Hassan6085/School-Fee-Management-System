from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QLabel
)
from PyQt6.QtCore import Qt
from db import get_connection
from backend.fee_operations import get_defaulters
from backend.setup_ops import get_campuses, get_classes
import os
from backend.data_emitter import DataEmitter  # New import

class DefaultersTab(QWidget):
    def __init__(self, current_user, emitter=None):  # Updated to accept emitter
        super().__init__()
        self.current_user = current_user
        self.emitter = emitter  # Store emitter for signal connection
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Filters Section
        filter_layout = QHBoxLayout()
        self.filter_campus = QComboBox()
        self.filter_class = QComboBox()
        filter_btn = QPushButton("Apply Filters")
        filter_btn.clicked.connect(self.load_defaulters_table)
        filter_layout.addWidget(QLabel("Campus:"))
        filter_layout.addWidget(self.filter_campus)
        filter_layout.addWidget(QLabel("Class:"))
        filter_layout.addWidget(self.filter_class)
        filter_layout.addWidget(filter_btn)
        layout.addLayout(filter_layout)

        # Defaulters Table
        self.defaulters_table = QTableWidget()
        self.defaulters_table.setColumnCount(9)
        self.defaulters_table.setHorizontalHeaderLabels(
            ['ID', 'Roll', 'Name', 'WhatsApp', 'Class', 'Campus', 'Year', 'Month', 'Pending']
        )
        self.defaulters_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.defaulters_table)

        self.setLayout(layout)
        self.load_campuses()
        self.load_defaulters_table()

        # Connect to emitter for real-time updates
        if self.emitter:
            self.emitter.data_changed.connect(self.reload_data)

        # Load stylesheet
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ui', 'styles.css'), 'r') as f:
            self.setStyleSheet(f.read())

    def load_campuses(self):
        self.filter_campus.clear()
        self.filter_campus.addItem("All Campuses", None)
        campuses = get_campuses()
        for cid, name in campuses:
            self.filter_campus.addItem(name, cid)
        self.filter_campus.currentIndexChanged.connect(self.on_filter_campus_changed)

    def on_filter_campus_changed(self, index):
        self.filter_class.clear()
        self.filter_class.addItem("All Classes", None)
        campus_id = self.filter_campus.currentData()
        if campus_id:
            classes = get_classes(campus_id)
            for cid, name, _ in classes:
                self.filter_class.addItem(name, cid)

    def load_defaulters_table(self):
        """Load the defaulters table, sorted by roll number, showing all records."""
        filters = {}
        if self.filter_campus.currentData():
            filters['campus_id'] = self.filter_campus.currentData()
        if self.filter_class.currentData():
            filters['class_id'] = self.filter_class.currentData()

        try:
            defaulters = get_defaulters(**filters)
            # Sort by roll number
            defaulters.sort(key=lambda x: x[1] or '')  # Sort by roll (index 1), handle None

            self.defaulters_table.setRowCount(len(defaulters))
            for i, defaulter in enumerate(defaulters):
                for j, val in enumerate(defaulter):
                    self.defaulters_table.setItem(i, j, QTableWidgetItem(str(val) if val is not None else ''))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load defaulters: {str(e)}")

    def reload_data(self):
        """Reload the defaulters table data."""
        self.load_defaulters_table()