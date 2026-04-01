from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget
)
from PyQt6.QtCore import Qt
import os

# Import Tabs
from ui.promotiontab import PromotionTab
from ui.setuptab import SetupTab
from ui.studentstab import StudentsTab
from ui.feestab import FeesTab
from ui.eventstab import EventsTab
from ui.reportstab import ReportsTab
from ui.backuptab import BackupTab
from ui.challantab import ChallanTab
from ui.defaulterstab import DefaultersTab
from ui.campusprofittab import CampusProfitTab
from ui.previousfeestab import PreviousFeesTab
from ui.usermanagementtab import UserManagementTab  # <--- NEW IMPORT

from backend.data_emitter import DataEmitter


class MainWindow(QMainWindow):
    def __init__(self, user_data=None):
        super().__init__()
        self.setWindowTitle('School Fee Manager - PyQt6')
        self.resize(1200, 780)

        self.current_user = user_data
        self.dark_mode = False
        self.current_index = -1

        # Central layout
        central = QWidget()
        main_layout = QHBoxLayout(central)

        # === SIDEBAR ===
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.sidebar_buttons = []

        # Shared data emitter
        self.emitter = DataEmitter()

        # Base Tabs
        base_tabs = [
            "Setup", "Students", "Fees", "Event Fees", "Reports",
            "Backup", "Challan", "Defaulters", "Previous Fees", "Promotion"
        ]

        self.tab_widgets = [
            SetupTab(self.current_user, self.emitter),
            StudentsTab(self.current_user, self.emitter),
            FeesTab(self.current_user, self.emitter),
            EventsTab(self.emitter),
            ReportsTab(self.emitter),
            BackupTab(self.current_user, self.emitter),
            ChallanTab(self.current_user, self.emitter),
            DefaultersTab(self.current_user, self.emitter),
            PreviousFeesTab(self.current_user, self.emitter),
            PromotionTab(self.current_user)
        ]

        # === Admin Only Tabs ===
        if self.current_user and self.current_user.get('role') == 'admin':
            # 1. Campus Profit
            base_tabs.append("Campus Profit")
            self.tab_widgets.append(CampusProfitTab(self.current_user, self.emitter))

            # 2. User Management (Now modular!)
            base_tabs.append("User Management")
            self.tab_widgets.append(UserManagementTab(self.current_user, self.emitter))

        # Stack for tab pages
        self.stack = QStackedWidget()
        for widget in self.tab_widgets:
            self.stack.addWidget(widget)

        # Sidebar Buttons Generation
        for idx, tab_name in enumerate(base_tabs):
            btn = QPushButton(tab_name)
            btn.setObjectName("sidebarBtn")
            btn.setFixedHeight(40)
            btn.clicked.connect(lambda checked, i=idx: self.on_tab_click(i))
            sidebar_layout.addWidget(btn)
            self.sidebar_buttons.append(btn)

        # Theme toggle button
        self.theme_btn = QPushButton("Toggle Theme")
        self.theme_btn.setObjectName("sidebarBtn")
        self.theme_btn.setFixedHeight(40)
        self.theme_btn.clicked.connect(self.toggle_theme)
        sidebar_layout.addWidget(self.theme_btn)

        # User info
        self.user_info = QLabel(
            f"Logged in as: {self.current_user.get('full_name', 'Unknown')} ({self.current_user.get('role', 'user')})"
            if self.current_user else "Not logged in"
        )
        self.user_info.setObjectName("userInfo")
        sidebar_layout.addWidget(self.user_info)

        sidebar_layout.addStretch()

        # Add sidebar and main stack
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack)
        self.setCentralWidget(central)

        # === Load Stylesheet ===
        try:
            with open(os.path.join(os.path.dirname(__file__), 'styles.css'), 'r') as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"⚠️ Failed to load stylesheet: {e}")

    # === Tab switching logic ===
    def on_tab_click(self, index):
        if self.current_index == index:
            current_widget = self.stack.widget(index)
            if hasattr(current_widget, 'reload_data'):
                current_widget.reload_data()
        else:
            self.stack.setCurrentIndex(index)
            self.current_index = index

    # === Theme toggle ===
    def toggle_theme(self):
        if self.dark_mode:
            self.apply_light_theme()
        else:
            self.apply_dark_theme()
        self.dark_mode = not self.dark_mode

    def apply_light_theme(self):
        self.setStyleSheet("background-color: #f5f5f5; color: #000;")

    def apply_dark_theme(self):
        self.setStyleSheet("background-color: #2b2b2b; color: #fff;")