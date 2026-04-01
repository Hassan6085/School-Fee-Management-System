from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QSpinBox,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QLabel
)
from PyQt6.QtCore import Qt
from db import get_connection
from backend.student_operations import get_students
from backend.fee_operations import add_historical_fee
import datetime

class PreviousFeesTab(QWidget):
    def __init__(self, current_user, emitter):
        super().__init__()
        self.current_user = current_user
        self.emitter = emitter
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Filters Section
        filter_layout = QHBoxLayout()
        self.filter_roll = QLineEdit()
        self.filter_roll.setPlaceholderText("Search by Roll")
        self.filter_roll.textChanged.connect(self.update_students)  # Dynamic update on text change
        self.filter_name = QLineEdit()
        self.filter_name.setPlaceholderText("Search by Name")
        self.filter_name.textChanged.connect(self.update_students)  # Dynamic update on text change
        self.filter_campus = QComboBox()
        self.filter_campus.addItem("All Campuses", None)
        self.filter_campus.currentIndexChanged.connect(self.update_students)  # Dynamic update on selection
        self.filter_class = QComboBox()
        self.filter_class.addItem("All Classes", None)
        self.filter_class.currentIndexChanged.connect(self.update_students)  # Dynamic update on selection
        filter_btn = QPushButton("Apply Filters")
        filter_btn.clicked.connect(self.load_fees_table)  # Still used for table filter
        filter_layout.addWidget(self.filter_roll)
        filter_layout.addWidget(self.filter_name)
        filter_layout.addWidget(self.filter_campus)
        filter_layout.addWidget(self.filter_class)
        filter_layout.addWidget(filter_btn)
        layout.addLayout(filter_layout)

        # Student Selection
        student_layout = QHBoxLayout()
        student_label = QLabel("Select Student:")
        self.student_combo = QComboBox()
        self.update_students()  # Initial load
        student_layout.addWidget(student_label)
        student_layout.addWidget(self.student_combo)
        layout.addLayout(student_layout)

        # Month and Amount Input
        month_layout = QHBoxLayout()
        self.year_combo = QComboBox()
        current_year = datetime.datetime.now().year
        for year in range(current_year - 2, current_year + 1):  # Last 2 years + current
            self.year_combo.addItem(str(year), year)
        self.year_combo.setCurrentIndex(2)  # Default to current year
        year_label = QLabel("Year:")
        self.month_combo = QComboBox()
        self.month_combo.addItems([
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ])
        month_label = QLabel("Month:")
        self.amount_spin = QSpinBox()
        self.amount_spin.setRange(0, 100_000)
        self.amount_spin.setValue(0)
        amount_label = QLabel("Pending Amount:")
        add_btn = QPushButton("Add Previous Fee")
        add_btn.clicked.connect(self.add_previous_fee)
        month_layout.addWidget(year_label)
        month_layout.addWidget(self.year_combo)
        month_layout.addWidget(month_label)
        month_layout.addWidget(self.month_combo)
        month_layout.addWidget(amount_label)
        month_layout.addWidget(self.amount_spin)
        month_layout.addWidget(add_btn)
        layout.addLayout(month_layout)

        # Fees Table
        self.fees_table = QTableWidget()
        self.fees_table.setColumnCount(5)
        self.fees_table.setHorizontalHeaderLabels(["Student Name", "Year", "Month", "Amount", "Status"])
        self.fees_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.fees_table)

        self.setLayout(layout)
        self.load_campuses()
        self.load_fees_table()

    def load_campuses(self):
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

    def update_students(self):
        """Update the student combo box based on current filters."""
        self.student_combo.clear()
        self.student_combo.addItem("Select Student", None)
        conn = get_connection()
        c = conn.cursor()
        q = "SELECT id, roll, name, campus_id, class_id FROM students WHERE 1=1"
        params = []
        if self.filter_roll.text().strip():
            q += " AND roll LIKE ?"
            params.append(f"%{self.filter_roll.text().strip()}%")
        if self.filter_name.text().strip():
            q += " AND name LIKE ?"
            params.append(f"%{self.filter_name.text().strip()}%")
        if self.filter_campus.currentData():
            q += " AND campus_id = ?"
            params.append(self.filter_campus.currentData())
        if self.filter_class.currentData():
            q += " AND class_id = ?"
            params.append(self.filter_class.currentData())
        c.execute(q, params)
        students = c.fetchall()
        conn.close()
        for sid, roll, name, campus_id, class_id in students:
            self.student_combo.addItem(f"{name} (Roll: {roll})", sid)

    def load_fees_table(self):
        selected_sid = self.student_combo.currentData()
        self.fees_table.setRowCount(0)
        if selected_sid:
            conn = get_connection()
            c = conn.cursor()
            q = '''
                SELECT s.name, f.year, f.month, f.pending, f.paid
                FROM fees f
                JOIN students s ON s.id = f.student_id
                WHERE f.student_id = ? AND f.year <= ?
            '''
            params = [selected_sid, datetime.datetime.now().year]
            if self.filter_roll.text().strip():
                q += " AND s.roll LIKE ?"
                params.append(f"%{self.filter_roll.text().strip()}%")
            if self.filter_name.text().strip():
                q += " AND s.name LIKE ?"
                params.append(f"%{self.filter_name.text().strip()}%")
            if self.filter_campus.currentData():
                q += " AND s.campus_id = ?"
                params.append(self.filter_campus.currentData())
            if self.filter_class.currentData():
                q += " AND s.class_id = ?"
                params.append(self.filter_class.currentData())
            q += " ORDER BY f.year DESC, f.month DESC"
            c.execute(q, params)
            fees = c.fetchall()
            conn.close()
            self.fees_table.setRowCount(len(fees))
            for i, (name, year, month_num, pending, paid) in enumerate(fees):
                month_name = datetime.datetime(2025, int(month_num), 1).strftime("%B")
                status = "Paid" if (paid or 0) >= (pending or 0) else "Pending"
                self.fees_table.setItem(i, 0, QTableWidgetItem(name))
                self.fees_table.setItem(i, 1, QTableWidgetItem(str(year)))
                self.fees_table.setItem(i, 2, QTableWidgetItem(month_name))
                self.fees_table.setItem(i, 3, QTableWidgetItem(str(pending or 0)))
                self.fees_table.setItem(i, 4, QTableWidgetItem(status))

    def add_previous_fee(self):
        if not self.current_user or self.current_user.get('role') != 'admin':
            QMessageBox.warning(self, "Error", "Admin privileges required")
            return

        student_id = self.student_combo.currentData()
        if not student_id:
            QMessageBox.warning(self, "Error", "Please select a student")
            return

        year = self.year_combo.currentData()
        month_name = self.month_combo.currentText()
        month_num = datetime.datetime.strptime(month_name, "%B").month
        amount = self.amount_spin.value()

        if amount <= 0:
            QMessageBox.warning(self, "Error", "Please enter a valid amount")
            return

        try:
            add_historical_fee(student_id, year, month_num, amount)
            QMessageBox.information(self, "Success", f"Added {amount} as previous fee for {month_name} {year}")
            self.load_fees_table()
            self.amount_spin.setValue(0)
            if self.emitter:
                self.emitter.data_changed.emit()
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to add previous fee: {str(e)}")

    def reload_data(self):
        self.update_students()
        self.load_fees_table()