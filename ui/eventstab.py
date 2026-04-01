from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, QSpinBox,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QLabel
)
from PyQt6.QtCore import Qt
from backend.student_operations import get_students
from backend.fee_operations import add_event_fee
from db import get_connection
import os

class EventsTab(QWidget):
    def __init__(self, emitter=None):  # Updated to accept emitter
        super().__init__()
        self.emitter = emitter  # Store emitter for signal emission
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Filters Section
        filter_layout = QHBoxLayout()
        self.filter_campus = QComboBox()
        self.filter_class = QComboBox()
        self.load_campuses()
        filter_layout.addWidget(QLabel("Campus:"))
        filter_layout.addWidget(self.filter_campus)
        filter_layout.addWidget(QLabel("Class:"))
        filter_layout.addWidget(self.filter_class)
        layout.addLayout(filter_layout)

        # Form Section
        form_layout = QHBoxLayout()
        form_label = QLabel("Manage Event Fees")
        self.ev_name = QLineEdit()
        self.ev_name.setPlaceholderText('Event Name')
        self.ev_amount = QSpinBox()
        self.ev_amount.setMaximum(1000000)
        self.ev_fee_id = QLineEdit()
        self.ev_fee_id.setPlaceholderText('Event Fee ID')

        # Add widgets to form layout horizontally
        form_layout.addWidget(form_label)
        form_layout.addWidget(self.filter_campus)  # Moved from filter_layout to form row
        form_layout.addWidget(self.filter_class)  # Moved from filter_layout to form row
        form_layout.addWidget(self.ev_name)
        form_layout.addWidget(self.ev_amount)
        form_layout.addWidget(self.ev_fee_id)

        # Action Dropdown
        self.action_combo = QComboBox()
        self.action_combo.addItems(['Select Action', 'Add Event Fee for Class', 'Mark Event Fee as Paid'])
        self.action_combo.currentIndexChanged.connect(self.on_action_changed)
        form_layout.addWidget(self.action_combo)

        layout.addLayout(form_layout)

        # Event Fee Table
        self.event_table = QTableWidget()
        self.event_table.setColumnCount(8)
        self.event_table.setHorizontalHeaderLabels(['ID', 'Student', 'Event', 'Amount', 'Paid', 'Pending', 'Class', 'Campus'])
        self.event_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.event_table)

        # Refresh Button
        refresh_btn = QPushButton('Refresh Events')
        refresh_btn.clicked.connect(self.load_event_table)
        layout.addWidget(refresh_btn)

        self.setLayout(layout)
        self.load_event_table()

        # Connect to emitter for real-time updates
        if self.emitter:
            self.emitter.data_changed.connect(self.reload_data)

        # Load stylesheet
        with open(os.path.join(os.path.dirname(__file__), 'styles.css'), 'r') as f:
            self.setStyleSheet(f.read())

    # --- Methods ---
    def load_campuses(self):
        self.filter_campus.clear()
        self.filter_campus.addItem("All Campuses", None)
        conn = get_connection()
        c = conn.cursor()
        c.execute('SELECT id, name FROM campuses')
        campuses = c.fetchall()
        conn.close()
        for cid, name in campuses:
            self.filter_campus.addItem(name, cid)
        self.filter_campus.currentIndexChanged.connect(self.on_filter_campus_changed)

    def on_filter_campus_changed(self, index):
        self.filter_class.clear()
        self.filter_class.addItem("All Classes", None)
        campus_id = self.filter_campus.currentData()
        if campus_id:
            conn = get_connection()
            c = conn.cursor()
            c.execute('SELECT id, name FROM classes WHERE campus_id=?', (campus_id,))
            classes = c.fetchall()
            conn.close()
            for cid, name in classes:
                self.filter_class.addItem(name, cid)

    def on_action_changed(self, index):
        action = self.action_combo.currentText()
        if action == 'Add Event Fee for Class':
            self.on_add_event_fee_for_class()
        elif action == 'Mark Event Fee as Paid':
            self.on_mark_event_fee_paid()
        elif action == 'Select Action':
            pass  # Do nothing when default option is selected

    def on_add_event_fee_for_class(self):
        class_id = self.filter_class.currentData()
        name = self.ev_name.text().strip()
        amt = self.ev_amount.value()

        if not class_id or not name or not amt:
            QMessageBox.warning(self, 'Error', 'Select a class and enter event name and amount')
            return

        try:
            conn = get_connection()
            c = conn.cursor()
            c.execute('SELECT id FROM students WHERE class_id=?', (class_id,))
            student_ids = c.fetchall()
            conn.close()

            for sid_tuple in student_ids:
                sid = sid_tuple[0]
                add_event_fee(sid, name, amt)

            QMessageBox.information(self, 'Added', f'Event fee added for {len(student_ids)} students')
            self.ev_name.clear()
            self.ev_amount.setValue(0)
            self.load_event_table()
            if self.emitter:
                self.emitter.data_changed.emit()  # Emit signal to update other tabs
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to add event fees: {str(e)}')

    def on_mark_event_fee_paid(self):
        fee_id = self.ev_fee_id.text().strip()
        if not fee_id:
            QMessageBox.warning(self, 'Error', 'Enter a valid Event Fee ID')
            return

        try:
            conn = get_connection()
            c = conn.cursor()
            c.execute('SELECT amount, paid, pending FROM event_fees WHERE id=?', (fee_id,))
            row = c.fetchone()
            if not row:
                QMessageBox.warning(self, 'Error', 'Invalid Event Fee ID')
                return
            total_amount, paid, pending = row

            if pending <= 0:
                QMessageBox.warning(self, 'Error', 'No pending amount to mark as paid')
                return

            new_paid = paid + pending
            new_pending = 0
            c.execute('UPDATE event_fees SET paid=?, pending=? WHERE id=?', (new_paid, new_pending, fee_id))
            conn.commit()
            conn.close()

            QMessageBox.information(self, 'Success', 'Event fee marked as paid')
            self.ev_fee_id.clear()
            self.load_event_table()
            if self.emitter:
                self.emitter.data_changed.emit()  # Emit signal to update other tabs
        except Exception as e:
            conn.rollback()
            conn.close()
            QMessageBox.warning(self, 'Error', f'Failed to mark fee as paid: {str(e)}')

    def load_event_table(self):
        conn = get_connection()
        c = conn.cursor()
        c.execute('''SELECT e.id, s.name, e.event_name, e.amount, e.paid, e.pending, c.name, cp.name
                     FROM event_fees e
                     JOIN students s ON e.student_id = s.id
                     JOIN classes c ON s.class_id = c.id
                     JOIN campuses cp ON s.campus_id = cp.id''')
        rows = c.fetchall()
        conn.close()

        self.event_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for j, val in enumerate(r):
                self.event_table.setItem(i, j, QTableWidgetItem(str(val) if val is not None else ''))

    def reload_data(self):
        """Reload the event table data."""
        self.load_event_table()