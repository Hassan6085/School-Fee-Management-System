from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QSpinBox,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QLabel, QCheckBox
)
from PyQt6.QtCore import Qt
from backend.fee_operations import (
    generate_monthly_fees, get_fees_with_students,
    add_payment, get_defaulters, mark_fee_unpaid  # New Import
)
from db import get_connection
from backend.student_operations import get_students
import os
import datetime


class FeesTab(QWidget):
    def __init__(self, current_user, emitter):
        super().__init__()
        self.current_user = current_user
        self.emitter = emitter
        self.is_defaulters_view = False
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Filters Section
        filter_layout = QHBoxLayout()
        self.filter_roll = QLineEdit()
        self.filter_roll.setPlaceholderText("Search by Roll")
        self.filter_name = QLineEdit()
        self.filter_name.setPlaceholderText("Search by Name")
        self.filter_campus = QComboBox()
        self.filter_class = QComboBox()
        filter_btn = QPushButton("Apply Filters")
        filter_btn.clicked.connect(self.load_fees_table)
        filter_layout.addWidget(self.filter_roll)
        filter_layout.addWidget(self.filter_name)
        filter_layout.addWidget(self.filter_campus)
        filter_layout.addWidget(self.filter_class)
        filter_layout.addWidget(filter_btn)
        layout.addLayout(filter_layout)

        # Form Section
        form_layout = QHBoxLayout()
        form_label = QLabel("Manage Fees")

        # Generation Inputs
        self.year_input = QSpinBox()
        self.year_input.setRange(2000, 2100)
        self.year_input.setValue(datetime.datetime.now().year)
        self.month_input = QComboBox()
        self.month_input.addItems([
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ])
        self.month_input.setCurrentIndex(datetime.datetime.now().month - 1)

        # Payment Inputs
        self.fee_id_input = QLineEdit()
        self.fee_id_input.setPlaceholderText("Fee ID")
        self.fee_id_input.setFixedWidth(80)

        # Amount Input
        self.amount_input = QSpinBox()
        self.amount_input.setRange(0, 1000000)
        self.amount_input.setValue(0)
        self.amount_input.setPrefix("Paid: ")

        # Runtime Discount Input (NEW)
        self.discount_input = QSpinBox()
        self.discount_input.setRange(0, 1000000)
        self.discount_input.setValue(0)
        self.discount_input.setPrefix("Disc: ")
        self.discount_input.setToolTip("Apply discount at time of payment")

        # Add checkbox for last month
        self.include_last_month = QCheckBox("Inc. Last Month")
        self.include_last_month.setChecked(False)

        form_layout.addWidget(form_label)
        form_layout.addWidget(self.year_input)
        form_layout.addWidget(self.month_input)
        form_layout.addWidget(self.fee_id_input)
        form_layout.addWidget(self.discount_input)  # Added here
        form_layout.addWidget(self.amount_input)
        form_layout.addWidget(self.include_last_month)

        # Action Dropdown
        self.action_combo = QComboBox()
        self.action_combo.addItems([
            'Select Action',
            'Generate Monthly Fees',
            'Add Payment',
            'Mark as Unpaid',  # New Option
            'View Defaulters'
        ])
        self.action_combo.currentIndexChanged.connect(self.on_action_changed)
        form_layout.addWidget(self.action_combo)

        layout.addLayout(form_layout)

        # Fees Table
        self.fees_table = QTableWidget()
        self.fees_table.setColumnCount(14)
        self.fees_table.setHorizontalHeaderLabels([
            'ID', 'Roll', 'Name', 'Campus', 'Class', 'Year', 'Month', 'Fee Amount',
            'Discount', 'Paid', 'Pending', 'Discount Type', 'Issue Date', 'Due Date'
        ])
        self.fees_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.fees_table.cellClicked.connect(self.on_table_click)  # Click to fill ID
        layout.addWidget(self.fees_table)

        self.setLayout(layout)
        self.load_campuses()
        self.load_fees_table()

        if self.emitter:
            self.emitter.data_changed.connect(self.reload_data)

        # Basic styling
        self.setStyleSheet("""
            QTableWidget::item:selected { background-color: #0078d7; color: white; }
        """)

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

    def on_table_click(self, row, col):
        # Auto-fill Fee ID when row is clicked
        try:
            fee_id = self.fees_table.item(row, 0).text()
            self.fee_id_input.setText(fee_id)

            # Optional: Auto-fill pending amount into amount box for convenience
            if not self.is_defaulters_view:
                pending_item = self.fees_table.item(row, 10)  # 10 is pending col
                if pending_item:
                    self.amount_input.setValue(int(pending_item.text()))
        except:
            pass

    def load_fees_table(self):
        filters = {}
        if self.filter_roll.text().strip():
            filters['roll'] = self.filter_roll.text().strip()
        if self.filter_name.text().strip():
            filters['name'] = self.filter_name.text().strip()
        if self.filter_campus.currentData():
            filters['campus_id'] = self.filter_campus.currentData()
        if self.filter_class.currentData():
            filters['class_id'] = self.filter_class.currentData()

        fees = get_fees_with_students(filters)
        self.fees_table.setRowCount(len(fees))
        self.fees_table.setColumnCount(14)
        self.fees_table.setHorizontalHeaderLabels([
            'ID', 'Roll', 'Name', 'Campus', 'Class', 'Year', 'Month', 'Fee Amount',
            'Discount', 'Paid', 'Pending', 'Discount Type', 'Issue Date', 'Due Date'
        ])

        for i, fee in enumerate(fees):
            for j, val in enumerate(fee):
                self.fees_table.setItem(i, j, QTableWidgetItem(str(val) if val is not None else ''))

    def reload_data(self):
        if self.is_defaulters_view:
            self.view_defaulters_action()
        else:
            self.load_fees_table()

    def on_action_changed(self, index):
        action = self.action_combo.currentText()
        if action == 'Generate Monthly Fees':
            self.generate_monthly_fees_action()
        elif action == 'Add Payment':
            self.add_payment_action()
        elif action == 'Mark as Unpaid':
            self.mark_unpaid_action()
        elif action == 'View Defaulters':
            self.view_defaulters_action()
        elif action == 'Select Action':
            if self.is_defaulters_view:
                self.load_fees_table()
                self.is_defaulters_view = False

        # Reset Combo
        self.action_combo.blockSignals(True)
        self.action_combo.setCurrentIndex(0)
        self.action_combo.blockSignals(False)

    def generate_monthly_fees_action(self):
        if not self.current_user or self.current_user.get('role') != 'admin':
            QMessageBox.warning(self, "Error", "Admin privileges required")
            return
        year = self.year_input.value()
        month = self.month_input.currentIndex() + 1
        try:
            created = generate_monthly_fees(year, month, self.include_last_month.isChecked())
            QMessageBox.information(self, "Success", f"Generated {created} new fee records")
            self.load_fees_table()
            if self.emitter:
                self.emitter.data_changed.emit()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to generate fees: {str(e)}")

    def add_payment_action(self):
        if not self.current_user or self.current_user.get('role') not in ['admin', 'user']:
            QMessageBox.warning(self, "Error", "You are not allowed to perform this action.")
            return

        fee_id = self.fee_id_input.text().strip()
        if not fee_id.isdigit():
            QMessageBox.warning(self, "Error", "Fee ID must be a number")
            return

        amount = self.amount_input.value()
        discount = self.discount_input.value()

        if amount <= 0 and discount <= 0:
            QMessageBox.warning(self, "Error", "Please enter a Payment Amount OR a Discount Amount")
            return

        confirm_msg = f"Apply Payment: {amount}"
        if discount > 0:
            confirm_msg += f"\nWith Runtime Discount: {discount}"

        reply = QMessageBox.question(self, "Confirm", confirm_msg,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        try:
            if add_payment(int(fee_id), amount, one_time_discount=discount):
                QMessageBox.information(
                    self, "Success",
                    f"Transaction successful!"
                )
                self.load_fees_table()
                self.fee_id_input.clear()
                self.amount_input.setValue(0)
                self.discount_input.setValue(0)
                if self.emitter:
                    self.emitter.data_changed.emit()
            else:
                QMessageBox.warning(self, "Error", "Invalid Fee ID")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to apply payment: {str(e)}")

    def mark_unpaid_action(self):
        # NEW FUNCTION: Mark Unpaid
        if not self.current_user or self.current_user.get('role') != 'admin':
            QMessageBox.warning(self, "Error", "Only Admin can revert payments.")
            return

        fee_id = self.fee_id_input.text().strip()
        if not fee_id.isdigit():
            QMessageBox.warning(self, "Error", "Please enter/select a Fee ID first.")
            return

        reply = QMessageBox.question(self, "Confirm Revert",
                                     "Are you sure you want to mark this fee as UNPAID?\nThis will reset the 'Paid' amount to 0.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if mark_fee_unpaid(int(fee_id)):
                    QMessageBox.information(self, "Success", "Fee marked as Unpaid.")
                    self.load_fees_table()
                    if self.emitter:
                        self.emitter.data_changed.emit()
                else:
                    QMessageBox.warning(self, "Error", "Invalid Fee ID")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to revert: {str(e)}")

    def view_defaulters_action(self):
        if not self.current_user or self.current_user.get('role') != 'admin':
            QMessageBox.warning(self, "Error", "Admin privileges required")
            return
        defaulters = get_defaulters()
        self.fees_table.setRowCount(len(defaulters))
        self.fees_table.setColumnCount(9)
        self.fees_table.setHorizontalHeaderLabels([
            'ID', 'Roll', 'Name', 'WhatsApp', 'Class', 'Campus', 'Year', 'Month', 'Pending'
        ])
        for i, defaulter in enumerate(defaulters):
            for j, val in enumerate(defaulter):
                self.fees_table.setItem(i, j, QTableWidgetItem(str(val) if val is not None else ''))
        self.is_defaulters_view = True