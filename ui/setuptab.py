from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QComboBox, QSpinBox, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt
from backend.setup_ops import add_campus, get_campuses, add_class, get_classes
import os
from backend.data_emitter import DataEmitter  # New import

class SetupTab(QWidget):
    def __init__(self, user_data=None, emitter=None, parent=None):
        super().__init__(parent)
        self.current_user = user_data  # store current user
        self.emitter = emitter  # Shared emitter for real-time updates
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        h = QHBoxLayout()

        self.campus_input = QLineEdit()
        self.campus_input.setPlaceholderText('Campus name')

        add_camp_btn = QPushButton('Add Campus')
        add_camp_btn.clicked.connect(self.on_add_campus)

        h.addWidget(self.campus_input)
        h.addWidget(add_camp_btn)
        layout.addLayout(h)

        h2 = QHBoxLayout()
        self.class_name_input = QLineEdit()
        self.class_name_input.setPlaceholderText('Class name (e.g. 9)')

        self.class_campus_combo = QComboBox()
        self.refresh_campuses_in_combo()

        self.class_fee_input = QSpinBox()
        self.class_fee_input.setMaximum(10000000)
        self.class_fee_input.setPrefix('Fee: ')

        add_class_btn = QPushButton('Add / Update Class')
        add_class_btn.clicked.connect(self.on_add_class)

        h2.addWidget(self.class_name_input)
        h2.addWidget(self.class_campus_combo)
        h2.addWidget(self.class_fee_input)
        h2.addWidget(add_class_btn)
        layout.addLayout(h2)

        self.setup_info = QTextEdit()
        self.setup_info.setReadOnly(True)
        refresh_btn = QPushButton('Refresh List')
        refresh_btn.clicked.connect(self.refresh_setup_info)
        layout.addWidget(self.setup_info)
        layout.addWidget(refresh_btn)

        self.setLayout(layout)

        # Load stylesheet
        with open(os.path.join(os.path.dirname(__file__), 'styles.css'), 'r') as f:
            self.setStyleSheet(f.read())

    # ---------- Handlers ----------
    def on_add_campus(self):
        name = self.campus_input.text().strip()
        if not name:
            QMessageBox.warning(self, 'Error', 'Enter campus name')
            return
        ok = add_campus(name)
        if ok:
            QMessageBox.information(self, 'Success', 'Campus added')
            self.campus_input.clear()
            self.refresh_campuses_in_combo()
            self.refresh_setup_info()
            if self.emitter:
                self.emitter.data_changed.emit()  # Emit signal to update other tabs
        else:
            QMessageBox.warning(self, 'Exists', 'Campus already exists')

    def refresh_campuses_in_combo(self):
        camps = get_campuses()
        self.class_campus_combo.clear()
        for cid, name in camps:
            self.class_campus_combo.addItem(name, cid)

    def on_add_class(self):
        name = self.class_name_input.text().strip()
        fee = self.class_fee_input.value()
        idx = self.class_campus_combo.currentIndex()
        if idx < 0:
            QMessageBox.warning(self, 'Error', 'Select campus')
            return
        campus_id = self.class_campus_combo.currentData()
        if not name:
            QMessageBox.warning(self, 'Error', 'Enter class name')
            return
        add_class(name, campus_id, fee)
        QMessageBox.information(self, 'Success', 'Class added or updated')
        self.class_name_input.clear()
        self.class_fee_input.setValue(0)
        self.refresh_setup_info()
        if self.emitter:
            self.emitter.data_changed.emit()  # Emit signal to update other tabs

    def refresh_setup_info(self):
        camps = get_campuses()
        txt = ''
        for cid, cname in camps:
            txt += f'Campus: {cname}\n'
            classes = get_classes(cid)
            for cl in classes:
                txt += f'  Class: {cl[1]}  Fee: {cl[2]}\n'
            txt += '\n'
        self.setup_info.setPlainText(txt)

    def reload_data(self):
        """Reload the setup information."""
        self.refresh_setup_info()