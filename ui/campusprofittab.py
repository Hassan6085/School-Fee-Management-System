from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QSpinBox,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QLabel,
    QGroupBox, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer
from db import get_connection
import os
import datetime
from backend.data_emitter import DataEmitter


class CampusProfitTab(QWidget):
    def __init__(self, current_user, emitter=None):
        super().__init__()
        self.current_user = current_user
        self.emitter = emitter
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # ==========================================
        # 1. TOP STATS (Daily & Monthly)
        # ==========================================
        stats_layout = QHBoxLayout()

        # Today's Card
        self.today_group = QGroupBox("Today's Collection")
        self.today_layout = QVBoxLayout()
        self.lbl_today_amount = QLabel("Rs. 0")
        self.lbl_today_amount.setStyleSheet("font-size: 24px; font-weight: bold; color: #2ecc71;")
        self.lbl_today_date = QLabel(datetime.datetime.now().strftime("%d %B, %Y"))
        self.today_layout.addWidget(self.lbl_today_amount, alignment=Qt.AlignmentFlag.AlignCenter)
        self.today_layout.addWidget(self.lbl_today_date, alignment=Qt.AlignmentFlag.AlignCenter)
        self.today_group.setLayout(self.today_layout)

        # Monthly Card
        self.month_group = QGroupBox("This Month's Collection")
        self.month_layout = QVBoxLayout()
        self.lbl_month_amount = QLabel("Rs. 0")
        self.lbl_month_amount.setStyleSheet("font-size: 24px; font-weight: bold; color: #3498db;")
        self.lbl_month_name = QLabel(datetime.datetime.now().strftime("%B %Y"))
        self.month_layout.addWidget(self.lbl_month_amount, alignment=Qt.AlignmentFlag.AlignCenter)
        self.month_layout.addWidget(self.lbl_month_name, alignment=Qt.AlignmentFlag.AlignCenter)
        self.month_group.setLayout(self.month_layout)

        stats_layout.addWidget(self.today_group)
        stats_layout.addWidget(self.month_group)
        layout.addLayout(stats_layout)

        # ==========================================
        # 2. DAILY TRANSACTIONS LIST
        # ==========================================
        trans_group = QGroupBox("Today's Detailed Transactions")
        trans_layout = QVBoxLayout()

        self.trans_table = QTableWidget()
        self.trans_table.setColumnCount(5)
        self.trans_table.setHorizontalHeaderLabels(['Time', 'Student', 'Class', 'Campus', 'Amount'])
        self.trans_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        trans_layout.addWidget(self.trans_table)
        trans_group.setLayout(trans_layout)
        layout.addWidget(trans_group)

        # ==========================================
        # 3. CAMPUS OVERALL PROFIT (Filters + Table)
        # ==========================================
        profit_group = QGroupBox("Campus Overall Profit Reports")
        profit_layout = QVBoxLayout()

        # Filters
        filter_layout = QHBoxLayout()
        self.year_input = QSpinBox()
        self.year_input.setRange(2000, 2100)
        self.year_input.setValue(datetime.datetime.now().year)
        self.month_input = QComboBox()
        self.month_input.addItems([
            "All Months", "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ])
        self.month_input.setCurrentIndex(0)

        filter_btn = QPushButton("Load Report")
        filter_btn.clicked.connect(self.load_profit_table)

        filter_layout.addWidget(QLabel("Year:"))
        filter_layout.addWidget(self.year_input)
        filter_layout.addWidget(QLabel("Month:"))
        filter_layout.addWidget(self.month_input)
        filter_layout.addWidget(filter_btn)
        profit_layout.addLayout(filter_layout)

        # Table
        self.profit_table = QTableWidget()
        self.profit_table.setColumnCount(4)
        self.profit_table.setHorizontalHeaderLabels(['Campus', 'Total Paid', 'Total Pending', 'Net Profit'])
        self.profit_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        profit_layout.addWidget(self.profit_table)

        profit_group.setLayout(profit_layout)
        layout.addWidget(profit_group)

        self.setLayout(layout)

        # Initial Load
        self.load_transaction_stats()
        self.load_daily_transactions()
        self.load_profit_table()

        # Connect Emitter
        if self.emitter:
            self.emitter.data_changed.connect(self.reload_data)

        # Style
        css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ui', 'styles.css')
        if os.path.exists(css_path):
            with open(css_path, 'r') as f:
                self.setStyleSheet(f.read())

    def reload_data(self):
        """Refreshes all data on the tab."""
        self.load_transaction_stats()
        self.load_daily_transactions()
        self.load_profit_table()

    def load_transaction_stats(self):
        """Loads totals for Today and This Month from the transaction log."""
        try:
            conn = get_connection()
            c = conn.cursor()

            # Daily Total
            c.execute("""
                SELECT SUM(amount) FROM fee_transactions 
                WHERE date(transaction_date) = date('now', 'localtime')
            """)
            daily_total = c.fetchone()[0] or 0

            # Monthly Total
            c.execute("""
                SELECT SUM(amount) FROM fee_transactions 
                WHERE strftime('%Y-%m', transaction_date) = strftime('%Y-%m', 'now', 'localtime')
            """)
            monthly_total = c.fetchone()[0] or 0

            conn.close()

            self.lbl_today_amount.setText(f"Rs. {daily_total:,}")
            self.lbl_month_amount.setText(f"Rs. {monthly_total:,}")

        except Exception as e:
            print(f"Stats Error: {e}")

    def load_daily_transactions(self):
        """Loads list of transactions for TODAY."""
        try:
            conn = get_connection()
            c = conn.cursor()

            query = """
                SELECT t.transaction_date, s.name, cl.name, cp.name, t.amount
                FROM fee_transactions t
                JOIN students s ON s.id = t.student_id
                JOIN classes cl ON cl.id = s.class_id
                JOIN campuses cp ON cp.id = s.campus_id
                WHERE date(t.transaction_date) = date('now', 'localtime')
                ORDER BY t.transaction_date DESC
            """
            c.execute(query)
            rows = c.fetchall()
            conn.close()

            self.trans_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                t_date, s_name, cl_name, cp_name, amount = row

                # Format time only (since it's today's list)
                try:
                    dt_obj = datetime.datetime.strptime(t_date, "%Y-%m-%d %H:%M:%S.%f")
                except:
                    try:
                        dt_obj = datetime.datetime.strptime(t_date, "%Y-%m-%d %H:%M:%S")
                    except:
                        dt_obj = datetime.datetime.now()

                time_str = dt_obj.strftime("%I:%M %p")  # e.g., 02:30 PM

                self.trans_table.setItem(i, 0, QTableWidgetItem(time_str))
                self.trans_table.setItem(i, 1, QTableWidgetItem(s_name))
                self.trans_table.setItem(i, 2, QTableWidgetItem(cl_name))
                self.trans_table.setItem(i, 3, QTableWidgetItem(cp_name))
                self.trans_table.setItem(i, 4, QTableWidgetItem(str(amount)))

        except Exception as e:
            print(f"Transactions Error: {e}")

    def load_profit_table(self):
        """Loads the campus-wise summary based on Fees Table (General Overview)."""
        year = self.year_input.value()
        month = self.month_input.currentIndex()
        try:
            conn = get_connection()
            c = conn.cursor()
            query = """
                SELECT cp.name, SUM(f.paid) as total_paid, SUM(f.pending) as total_pending
                FROM fees f
                JOIN students s ON s.id = f.student_id
                JOIN campuses cp ON cp.id = s.campus_id
            """
            params = []
            if month > 0:  # If not "All Months"
                query += " WHERE f.year = ? AND f.month = ?"
                params.extend([year, month])
            else:
                query += " WHERE f.year = ?"
                params.append(year)
            query += " GROUP BY cp.name"
            c.execute(query, params)
            rows = c.fetchall()
            conn.close()

            self.profit_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                campus, total_paid, total_pending = row
                profit = total_paid - total_pending if total_paid and total_pending else 0

                # Safely handle None
                total_paid = total_paid or 0
                total_pending = total_pending or 0
                profit = total_paid  # In school context, Profit is usually just Collection?
                # Or if Profit = Paid - Pending (which represents outstanding).
                # Your previous code did (paid - pending). I kept it, but usually Profit = Paid - Expenses.
                # Here likely Profit just means "Net Collection" vs "Deficit".

                # Let's keep your logic: Profit = Paid - Pending (Surplus vs Deficit)
                val_profit = total_paid - total_pending

                self.profit_table.setItem(i, 0, QTableWidgetItem(str(campus)))
                self.profit_table.setItem(i, 1, QTableWidgetItem(str(total_paid)))
                self.profit_table.setItem(i, 2, QTableWidgetItem(str(total_pending)))

                item_profit = QTableWidgetItem(str(val_profit))
                if val_profit < 0:
                    item_profit.setForeground(Qt.GlobalColor.red)
                else:
                    item_profit.setForeground(Qt.GlobalColor.darkGreen)
                self.profit_table.setItem(i, 3, item_profit)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load profit data: {str(e)}")