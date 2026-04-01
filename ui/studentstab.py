from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QSpinBox,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QLabel
)
from PyQt6.QtCore import Qt
from db import get_connection
from backend.setup_ops import get_campuses, get_classes
from backend.student_operations import add_student, get_students, update_student, delete_student
import os

class StudentsTab(QWidget):
    def __init__(self, current_user, emitter):
        super().__init__()
        self.current_user = current_user
        self.emitter = emitter  # Shared emitter for real-time updates
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Filters Section
        filter_layout = QHBoxLayout()
        self.filter_name = QLineEdit()
        self.filter_name.setPlaceholderText("Search by Name")
        self.filter_class = QComboBox()
        self.filter_campus = QComboBox()
        filter_btn = QPushButton("Apply Filters")
        filter_btn.clicked.connect(self.load_students_table)
        filter_layout.addWidget(self.filter_name)
        filter_layout.addWidget(self.filter_campus)
        filter_layout.addWidget(self.filter_class)
        filter_layout.addWidget(filter_btn)
        layout.addLayout(filter_layout)

        # Form Section
        form_layout = QHBoxLayout()

        self.roll_input = QLineEdit()
        self.roll_input.setPlaceholderText("Roll Number")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Student Name")
        self.father_input = QLineEdit()
        self.father_input.setPlaceholderText("Father's Name")
        self.campus_combo = QComboBox()
        self.class_combo = QComboBox()
        self.whatsapp_input = QLineEdit()
        self.whatsapp_input.setPlaceholderText("WhatsApp Number")
        self.discount_type_combo = QComboBox()
        self.discount_type_combo.addItems(['none', 'amount', 'percent'])
        self.discount_value_spin = QSpinBox()
        self.discount_value_spin.setRange(0, 100_000)
        self.discount_value_spin.setValue(0)

        # Add widgets to form layout horizontally
        form_layout.addWidget(self.roll_input)
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.father_input)
        form_layout.addWidget(self.campus_combo)
        form_layout.addWidget(self.class_combo)
        form_layout.addWidget(self.whatsapp_input)
        form_layout.addWidget(self.discount_type_combo)
        form_layout.addWidget(self.discount_value_spin)

        # Action Dropdown
        self.action_combo = QComboBox()
        self.update_action_dropdown()
        self.action_combo.currentIndexChanged.connect(self.on_action_changed)
        form_layout.addWidget(self.action_combo)

        layout.addLayout(form_layout)

        # Students Table
        self.student_table = QTableWidget()
        self.student_table.setColumnCount(9)
        self.student_table.setHorizontalHeaderLabels(
            ['ID', 'Roll', 'Name', 'Father', 'Class', 'Campus', 'WhatsApp', 'Discount Type', 'Discount Value']
        )
        self.student_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.student_table)

        self.setLayout(layout)
        self.load_campuses()
        self.load_students_table()

        # Load stylesheet
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ui', 'styles.css'), 'r') as f:
            self.setStyleSheet(f.read())

    def load_campuses(self):
        self.campus_combo.clear()
        self.filter_campus.clear()
        self.campus_combo.addItem("Select Campus", None)
        self.filter_campus.addItem("All Campuses", None)
        campuses = get_campuses()
        for cid, name in campuses:
            self.campus_combo.addItem(name, cid)
            self.filter_campus.addItem(name, cid)
        self.campus_combo.currentIndexChanged.connect(self.on_campus_changed)
        self.filter_campus.currentIndexChanged.connect(self.on_filter_campus_changed)

    def on_campus_changed(self, index):
        self.class_combo.clear()
        self.class_combo.addItem("Select Class", None)
        campus_id = self.campus_combo.currentData()
        if campus_id:
            classes = get_classes(campus_id)
            for cid, name, _ in classes:
                self.class_combo.addItem(name, cid)

    def on_filter_campus_changed(self, index):
        self.filter_class.clear()
        self.filter_class.addItem("All Classes", None)
        campus_id = self.filter_campus.currentData()
        if campus_id:
            classes = get_classes(campus_id)
            for cid, name, _ in classes:
                self.filter_class.addItem(name, cid)

    def load_students_table(self):
        filters = {}
        if self.filter_name.text().strip():
            filters['name'] = self.filter_name.text().strip()
        if self.filter_campus.currentData():
            filters['campus_id'] = self.filter_campus.currentData()
        if self.filter_class.currentData():
            filters['class_id'] = self.filter_class.currentData()

        students = get_students(**filters)
        self.student_table.setRowCount(len(students))
        for i, student in enumerate(students):
            sid, roll, name, father, class_id, campus_id, whatsapp, discount_type, discount_value = student
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT name FROM classes WHERE id=?", (class_id,))
            class_result = c.fetchone()  # Fetch once
            class_name = class_result[0] if class_result else "Unknown"
            c.execute("SELECT name FROM campuses WHERE id=?", (campus_id,))
            campus_result = c.fetchone()  # Fetch once
            campus_name = campus_result[0] if campus_result else "Unknown"
            conn.close()
            values = [str(sid), roll, name, father, class_name, campus_name, whatsapp, discount_type, str(discount_value)]
            for j, val in enumerate(values):
                self.student_table.setItem(i, j, QTableWidgetItem(val))

    def reload_data(self):
        """Reload the students table data."""
        self.load_students_table()

    def update_action_dropdown(self):
        self.action_combo.clear()
        self.action_combo.addItem("Select Action")
        if self.current_user and self.current_user.get('role') == 'admin':
            self.action_combo.addItems(['Add Student', 'Edit Student', 'Update Student', 'Delete Student'])
        else:
            self.action_combo.addItems(['Print Challan', 'Add Payment'])

    def on_action_changed(self, index):
        action = self.action_combo.currentText()
        if action == 'Add Student' and self.current_user.get('role') == 'admin':
            self.on_add_student()
        elif action == 'Edit Student' and self.current_user.get('role') == 'admin':
            self.on_edit_student()
        elif action == 'Update Student' and self.current_user.get('role') == 'admin':
            self.on_update_student()
        elif action == 'Delete Student' and self.current_user.get('role') == 'admin':
            self.on_delete_student()
        elif action == 'Print Challan':
            self.on_print_challan()
        elif action == 'Add Payment':
            self.on_add_payment()
        elif action == 'Select Action':
            pass  # Do nothing when default option is selected

    def on_add_student(self):
        if not self.current_user or self.current_user.get('role') != 'admin':
            QMessageBox.warning(self, "Error", "Admin privileges required")
            return

        roll = self.roll_input.text().strip()
        name = self.name_input.text().strip()
        father = self.father_input.text().strip()
        campus_id = self.campus_combo.currentData()
        class_id = self.class_combo.currentData()
        whatsapp = self.whatsapp_input.text().strip()
        discount_type = self.discount_type_combo.currentText()
        discount_value = self.discount_value_spin.value()

        if not all([roll, name, father, campus_id, class_id]):
            QMessageBox.warning(self, "Error", "Please fill all required fields")
            return

        try:
            add_student(self.current_user, roll, name, father, class_id, campus_id, whatsapp, discount_type, discount_value)
            QMessageBox.information(self, "Success", "Student added successfully")
            self.load_students_table()
            self.clear_form()
            self.action_combo.setCurrentIndex(0)
            if self.emitter:
                self.emitter.data_changed.emit()  # Emit signal to update other tabs
        except PermissionError as e:
            QMessageBox.warning(self, "Error", str(e))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to add student: {str(e)}")

    def on_edit_student(self):
        if not self.current_user or self.current_user.get('role') != 'admin':
            QMessageBox.warning(self, "Error", "Admin privileges required")
            return

        selected_row = self.student_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Error", "Please select a student first")
            return

        sid = int(self.student_table.item(selected_row, 0).text())
        conn = get_connection()
        c = conn.cursor()
        c.execute(
            "SELECT roll, name, father, class_id, campus_id, whatsapp, discount_type, discount_value FROM students WHERE id=?",
            (sid,)
        )
        student = c.fetchone()
        conn.close()

        if student:
            roll, name, father, class_id, campus_id, whatsapp, discount_type, discount_value = student
            self.roll_input.setText(roll)
            self.name_input.setText(name)
            self.father_input.setText(father)
            for i in range(self.campus_combo.count()):
                if self.campus_combo.itemData(i) == campus_id:
                    self.campus_combo.setCurrentIndex(i)
                    self.on_campus_changed(i)
                    break
            for i in range(self.class_combo.count()):
                if self.class_combo.itemData(i) == class_id:
                    self.class_combo.setCurrentIndex(i)
                    break
            self.whatsapp_input.setText(whatsapp)
            self.discount_type_combo.setCurrentText(discount_type)
            self.discount_value_spin.setValue(discount_value)

    def on_update_student(self):
        if not self.current_user or self.current_user.get('role') != 'admin':
            QMessageBox.warning(self, "Error", "Admin privileges required")
            return

        selected_row = self.student_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Error", "Please select a student first")
            return

        sid = int(self.student_table.item(selected_row, 0).text())
        roll = self.roll_input.text().strip()
        name = self.name_input.text().strip()
        father = self.father_input.text().strip()
        campus_id = self.campus_combo.currentData()
        class_id = self.class_combo.currentData()
        whatsapp = self.whatsapp_input.text().strip()
        discount_type = self.discount_type_combo.currentText()
        discount_value = self.discount_value_spin.value()

        if not all([roll, name, father, campus_id, class_id]):
            QMessageBox.warning(self, "Error", "Please fill all required fields")
            return

        try:
            update_student(self.current_user, sid, roll=roll, name=name, father=father, class_id=class_id, campus_id=campus_id, whatsapp=whatsapp, discount_type=discount_type, discount_value=discount_value)
            QMessageBox.information(self, "Success", "Student updated successfully")
            self.load_students_table()
            self.clear_form()
            self.action_combo.setCurrentIndex(0)
            if self.emitter:
                self.emitter.data_changed.emit()  # Emit signal to update other tabs
        except PermissionError as e:
            QMessageBox.warning(self, "Error", str(e))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to update student: {str(e)}")

    def on_delete_student(self):
        if not self.current_user or self.current_user.get('role') != 'admin':
            QMessageBox.warning(self, "Error", "Admin privileges required")
            return

        selected_row = self.student_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Error", "Please select a student first")
            return

        sid = int(self.student_table.item(selected_row, 0).text())
        name = self.student_table.item(selected_row, 2).text()

        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete student '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                delete_student(self.current_user, sid)
                QMessageBox.information(self, "Success", "Student deleted successfully")
                self.load_students_table()
                self.clear_form()
                self.action_combo.setCurrentIndex(0)
                if self.emitter:
                    self.emitter.data_changed.emit()  # Emit signal to update other tabs
            except PermissionError as e:
                QMessageBox.warning(self, "Error", str(e))
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete student: {str(e)}")

    def on_print_challan(self):
        selected_row = self.student_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Error", "Please select a student first")
            return
        sid = int(self.student_table.item(selected_row, 0).text())
        QMessageBox.information(self, "Print Challan", f"Printing challan for student ID: {sid}")

    def on_add_payment(self):
        selected_row = self.student_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Error", "Please select a student first")
            return
        sid = int(self.student_table.item(selected_row, 0).text())
        QMessageBox.information(self, "Add Payment", f"Adding payment for student ID: {sid}")

    def clear_form(self):
        self.roll_input.clear()
        self.name_input.clear()
        self.father_input.clear()
        self.campus_combo.setCurrentIndex(0)
        self.class_combo.setCurrentIndex(0)
        self.whatsapp_input.clear()
        self.discount_type_combo.setCurrentText('none')
        self.discount_value_spin.setValue(0)