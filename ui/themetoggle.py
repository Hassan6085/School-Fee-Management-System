from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
import os

class ThemeToggle(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.is_dark = False

        layout = QVBoxLayout()
        self.btn = QPushButton("Toggle Dark/Light Theme")
        self.btn.clicked.connect(self.toggle_theme)
        layout.addWidget(self.btn)

        self.setLayout(layout)

        # Load existing stylesheet
        with open(os.path.join(os.path.dirname(__file__), 'ui', 'styles.css'), 'r') as f:
            self.main_window.parent().parent().setStyleSheet(f.read())

    def toggle_theme(self):
        app = self.main_window.parent().parent()
        self.is_dark = not self.is_dark

        # Use class-based styling from styles.css
        if self.is_dark:
            app.setStyleSheet(f"{app.styleSheet()} .dark-theme {{}}")
        else:
            # Reset to base stylesheet to remove dark-theme effect
            with open(os.path.join(os.path.dirname(__file__), 'ui', 'styles.css'), 'r') as f:
                app.setStyleSheet(f.read())

        # Update button text based on theme
        self.btn.setText("Toggle Light/Dark Theme" if self.is_dark else "Toggle Dark/Light Theme")