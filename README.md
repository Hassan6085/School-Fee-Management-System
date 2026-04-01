# 🏫 School Fee Management System

A comprehensive, robust, and user-friendly desktop application built with Python and PyQt6. This system is designed to streamline school administrative tasks, manage student fees, track campus profitability, and ensure data safety with automated cloud backups.

---

## ✨ Key Features

* **Multi-Campus Management:** Seamlessly add and manage multiple campuses and classes within a single unified system.
* **Advanced Fee & Discount Handling:** * Manage fixed monthly fees for different classes.
  * Apply customized discounts to individual students (both fixed monthly discounts and runtime adjustments).
* **Role-Based Access Control:** Secure user management system to ensure that staff and admins only have access to their authorized sections.
* **Campus Profitability Tracking:** Automatically calculate and track financial performance and profits across different campuses.
* **Automated Cloud Backups:** Integrated with the Google Drive API to automatically back up the SQLite database, ensuring zero data loss.
* **Modern Desktop UI:** A responsive and intuitive user interface built from the ground up using PyQt6.

---

## 🛠️ Tech Stack

* **Language:** Python 3.x
* **GUI Framework:** PyQt6
* **Database:** SQLite3
* **Cloud Integration:** Google Drive API (for automated database backups)

---

## 📁 Project Structure

The repository is modular and structured for scalability and easy maintenance:

```text
School-Fee-Management-System/
│
├── backend/                # Contains core logic, API operations, and backup scripts
├── ui/                     # PyQt6 UI components, stylesheets, and layouts
├── db.py                   # Database connection and initialization handling
├── login.py                # Authentication and login module
├── main.py                 # Application entry point and main window orchestration
├── requirements.txt        # Python dependencies list
└── README.md               # Project documentation
