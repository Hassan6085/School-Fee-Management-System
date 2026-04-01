# ui/promotiontab.py
import os
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton,
    QLabel, QMessageBox, QSpinBox
)
from backend.setup_ops import get_campuses, get_classes
from db import get_connection

class PromotionTab(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("<h2>Promote Students to Next Class</h2>")
        title.setStyleSheet("color: #1E293B; margin: 20px;")
        layout.addWidget(title)

        # Campus Selection
        campus_layout = QHBoxLayout()
        campus_layout.addWidget(QLabel("From Campus:"))
        self.from_campus = QComboBox()
        self.from_campus.addItem("Select Campus", None)
        campuses = get_campuses()
        for cid, name in campuses:
            self.from_campus.addItem(name, cid)
        self.from_campus.currentIndexChanged.connect(self.load_from_classes)
        campus_layout.addWidget(self.from_campus)
        layout.addLayout(campus_layout)

        # From Class
        class_layout = QHBoxLayout()
        class_layout.addWidget(QLabel("From Class:"))
        self.from_class = QComboBox()
        self.from_class.addItem("Select Class", None)
        class_layout.addWidget(self.from_class)
        layout.addLayout(class_layout)

        # To Class
        to_layout = QHBoxLayout()
        to_layout.addWidget(QLabel("Promote To:"))
        self.to_class = QComboBox()
        self.to_class.addItem("Select Class", None)
        to_layout.addWidget(self.to_class)
        layout.addLayout(to_layout)

        # Academic Year
        year_layout = QHBoxLayout()
        year_layout.addWidget(QLabel("New Academic Year:"))
        self.new_year = QSpinBox()
        self.new_year.setRange(2020, 2100)
        self.new_year.setValue(datetime.now().year + 1)
        year_layout.addWidget(self.new_year)
        layout.addLayout(year_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        preview_btn = QPushButton("Preview Students")
        preview_btn.clicked.connect(self.preview_promotion)
        promote_btn = QPushButton("Promote Students")
        promote_btn.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold;")
        promote_btn.clicked.connect(self.promote_students)
        btn_layout.addWidget(preview_btn)
        btn_layout.addWidget(promote_btn)
        layout.addLayout(btn_layout)

        # Result Label
        self.result_label = QLabel("")
        self.result_label.setStyleSheet("margin-top: 20px; font-size: 14px;")
        layout.addWidget(self.result_label)

        layout.addStretch()
        self.setLayout(layout)

        # Load CSS
        css_path = os.path.join(os.path.dirname(__file__), 'styles.css')
        if os.path.exists(css_path):
            with open(css_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())

    def load_from_classes(self):
        self.from_class.clear()
        self.from_class.addItem("Select Class", None)
        self.to_class.clear()
        self.to_class.addItem("Select Class", None)

        campus_id = self.from_campus.currentData()
        if not campus_id:
            return

        classes = get_classes(campus_id)
        for cid, name, _ in classes:
            self.from_class.addItem(name, cid)
            self.to_class.addItem(name, cid)
        self.from_class.currentIndexChanged.connect(self.update_to_class)

    def update_to_class(self):
        current_class_id = self.from_class.currentData()
        if not current_class_id:
            return
        # Suggest next class (e.g., 9 → 10)
        current_name = self.from_class.currentText()
        try:
            num = int(''.join(filter(str.isdigit, current_name)))
            next_num = num + 1
            suggested = current_name.replace(str(num), str(next_num))
            index = self.to_class.findText(suggested)
            if index != -1:
                self.to_class.setCurrentIndex(index)
        except:
            pass

    def preview_promotion(self):
        if not self.validate_inputs():
            return
        count = self.get_student_count()
        if count == 0:
            self.result_label.setText("<span style='color: orange;'>No students found in selected class.</span>")
        else:
            self.result_label.setText(
                f"<span style='color: green;'><b>{count}</b> students will be promoted to "
                f"<b>{self.to_class.currentText()}</b> ({self.new_year.value()})</span>"
            )

    def promote_students(self):
        if not self.validate_inputs():
            return

        reply = QMessageBox.question(
            self, "Confirm Promotion",
            f"Promote {self.get_student_count()} students to {self.to_class.currentText()}?\n\n"
            "This action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            count = self.promote_all_students()
            QMessageBox.information(
                self, "Success",
                f"Successfully promoted <b>{count}</b> students to <b>{self.to_class.currentText()}</b>!"
            )
            self.result_label.setText(f"<span style='color: green;'>Promotion completed!</span>")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Promotion failed:\n{str(e)}")

    def validate_inputs(self):
        if not self.from_campus.currentData():
            QMessageBox.warning(self, "Error", "Please select campus")
            return False
        if not self.from_class.currentData():
            QMessageBox.warning(self, "Error", "Please select from class")
            return False
        if not self.to_class.currentData():
            QMessageBox.warning(self, "Error", "Please select destination class")
            return False
        if self.from_class.currentData() == self.to_class.currentData():
            QMessageBox.warning(self, "Error", "From and To class cannot be same!")
            return False
        return True

    def get_student_count(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM students WHERE class_id = ?",
                    (self.from_class.currentData(),))
        count = cur.fetchone()[0]
        conn.close()
        return count

    def promote_all_students(self):
        conn = get_connection()
        cur = conn.cursor()
        from_class_id = self.from_class.currentData()
        to_class_id = self.to_class.currentData()
        new_year = self.new_year.value()

        # Update class_id for all students
        cur.execute("UPDATE students SET class_id = ? WHERE class_id = ?",
                    (to_class_id, from_class_id))

        # Optional: Clear current year fees if needed
        # cur.execute("DELETE FROM fees WHERE year = ? AND student_id IN (SELECT id FROM students WHERE class_id = ?)",
        #             (datetime.now().year, to_class_id))

        conn.commit()
        count = cur.rowcount
        conn.close()
        return count