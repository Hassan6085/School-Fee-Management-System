import sys
import os
from PyQt6.QtWidgets import QApplication

from db import init_db
from login import LoginDialog
from ui.main_window import MainWindow

# ✅ Helper function for PyInstaller exe support
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller exe"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    try:
        init_db()  # Initialize database
    except Exception as e:
        print(f"Failed to initialize database: {e}", file=sys.stderr)
        sys.exit(1)

    app = QApplication(sys.argv)
    login_dialog = LoginDialog()
    if login_dialog.exec():
        user_data = login_dialog.get_credentials()
        if user_data:
            main_window = MainWindow(user_data=user_data)
            main_window.show()
            sys.exit(app.exec())
    # Exit if login is cancelled or closed
    sys.exit(0)

if __name__ == "__main__":
    main()