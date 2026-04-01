import os
import re
import datetime
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton,
    QMessageBox, QFileDialog, QLabel
)
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from backend.setup_ops import get_campuses, get_classes
from db import get_connection
from backend.data_emitter import DataEmitter


# ==================== PYINSTALLER SAFE PATH ====================
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ==================== DRAWING HELPERS ====================
def draw_header(c, x, y, w, data):
    shift = 12.7

    # ---- LOGO ----
    logo_path = resource_path(os.path.join("ui", "logo.png"))

    if os.path.exists(logo_path):
        try:
            logo_width = 15 * mm
            logo_height = 12 * mm
            c.drawImage(
                logo_path,
                x + 2 * mm,
                y - logo_height + 2,
                logo_width,
                logo_height,
                preserveAspectRatio=True,
                mask='auto'
            )
        except Exception as e:
            print(f"[LOGO ERROR] {e}")

    # ---- campus name ----
    c.setFont('Helvetica-Bold', 17)
    campus_text = data['campus']
    box_w = 150
    box_h = 25
    box_x = (x + (w - box_w) / 2)
    box_y = y - shift - box_h + 5

    c.rect(box_x, box_y, box_w, box_h, stroke=1, fill=0)
    c.drawCentredString(box_x + box_w / 2, box_y + (box_h / 2) - 4, campus_text)

    # ---- school name ----
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(x + w / 2, box_y - 12, data['school'])

    # ---- issue date ----
    right_x = x + w - 6 * mm
    c.setFont('Helvetica', 10)
    c.drawRightString(right_x + 7, y - 60 - shift, 'ISSUE DATE')
    c.drawRightString(right_x + 7, y - 70 - shift, data['issue_date'])


def draw_student_info(c, x, y, w, data):
    c.setFont('Helvetica', 10)
    left_col_x = x + 6 * mm
    line_h = 12
    shift = 35.1
    labels = ['Fee Month:', 'Adm No.:', 'Name:', "Father's Name:", 'Class:', 'Section']
    values = [data['fee_month'], data['Roll'], data['Name'], data['Father'], data['Class'], '']
    cur_y = y - shift
    for lbl, val in zip(labels, values):
        c.drawString(left_col_x, cur_y, lbl)
        c.drawString(left_col_x + 70, cur_y, str(val))
        cur_y -= line_h


def draw_particulars_table(c, x, y, w, data):
    table_x = x + 6 * mm
    table_w = w - 12 * mm
    row_h = 14
    shift = 50.8
    y = y - shift

    sr_col_w = 30
    amt_col_w = 50

    c.setFont('Helvetica-Bold', 10)
    c.rect(table_x, y - row_h, table_w, row_h, stroke=1, fill=0)
    c.drawString(table_x + 8, y - row_h + 4, 'Sr. #')
    c.drawString(table_x + sr_col_w + 8, y - row_h + 4, 'PARTICULARS')
    c.drawRightString(table_x + table_w - 8, y - row_h + 4, 'Amount')

    c.line(table_x + sr_col_w, y - row_h, table_x + sr_col_w, y - row_h - (len(data['particulars']) * row_h))
    c.line(table_x + table_w - amt_col_w, y - row_h, table_x + table_w - amt_col_w,
           y - row_h - (len(data['particulars']) * row_h))

    c.setFont('Helvetica', 9)
    cur_y = y - row_h
    for i, (part, amt) in enumerate(data['particulars'], start=1):
        cur_y -= row_h
        c.rect(table_x, cur_y, table_w, row_h, stroke=1, fill=0)
        c.drawCentredString(table_x + sr_col_w / 2, cur_y + 4, str(i))
        c.drawString(table_x + sr_col_w + 6, cur_y + 4, str(part))
        c.drawRightString(table_x + table_w - 8, cur_y + 4, str(amt))

    payable_y = cur_y - 18
    c.setFont('Helvetica-Bold', 12)
    c.drawString(table_x, payable_y + 4, 'Payable Amount:')
    c.drawRightString(table_x + table_w - 6, payable_y + 4, str(data['payable']))


def draw_footer(c, x, y, w, data):
    left_x = x + 6 * mm
    c.setFont('Helvetica-Bold', 11)
    notes_y = y + 50
    c.drawString(left_x, notes_y + 10, 'Due Date:')
    c.drawString(left_x + 60, notes_y + 10, data['due_date'])
    sig_y = notes_y - 10
    c.line(left_x, sig_y, left_x + 60 * mm, sig_y)
    c.setFont('Helvetica', 9)
    c.drawString(left_x, sig_y + 3, 'Signature:')
    c.setFont('Helvetica', 8)
    small_notes_y = sig_y - 14
    c.drawString(left_x, small_notes_y, 'The fee must be paid by the due date.')
    c.drawString(left_x, small_notes_y - 10, 'Late Payment surcharge will be charged @50 per day.')
    c.drawString(left_x, small_notes_y - 20, 'Student will be struck off if fee not paid within month.')


def draw_single_challan_column(c, x, y_top, w, data):
    """Draws one column (e.g. Student Copy) on the canvas"""
    total_h = 185 * mm
    c.rect(x, y_top - total_h, w, total_h, stroke=1, fill=0)
    draw_header(c, x, y_top - 10, w, data)
    draw_student_info(c, x, y_top - 40, w, data)
    draw_particulars_table(c, x, y_top - 110, w, data)
    draw_footer(c, x, y_top - total_h + 40, w, data)


# ==================== PDF GENERATOR (COMBINED) ====================
def generate_class_challans_single_file(output_path, class_id, year, month_name):
    """
    Generates a single PDF file containing challans for all students in the class.
    Uses selected Year and Month for calculations.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Convert month name to number for DB queries and Date Logic
    try:
        cur_month_num = datetime.datetime.strptime(month_name, "%B").month
    except ValueError:
        # Fallback to current month if error
        cur_month_num = datetime.datetime.now().month

    # Get Students and their specific monthly fee status
    # Note: We filter by the SELECTED year and month
    cursor.execute('''SELECT s.id, s.roll, s.name, s.father, cl.name, ca.name, s.whatsapp,
                             COALESCE(f.fee_amount,0), COALESCE(f.paid,0), COALESCE(f.pending,0), cl.default_fee
                      FROM students s
                      JOIN classes cl ON s.class_id = cl.id
                      JOIN campuses ca ON s.campus_id = ca.id
                      LEFT JOIN fees f ON s.id = f.student_id AND f.year = ? AND f.month = ?
                      WHERE s.class_id = ? ORDER BY s.roll''', (year, cur_month_num, class_id))
    students = cursor.fetchall()

    if not students:
        conn.close()
        raise ValueError(f"No students found for the selected class in {month_name} {year}.")

    # ----------------------------------------------------
    # Calculate Fixed Due Date (10th of the SELECTED month)
    # ----------------------------------------------------
    try:
        due_date_obj = datetime.date(int(year), cur_month_num, 10)
        fixed_due_date = due_date_obj.strftime('%d/%m/%Y')
    except ValueError:
        # Fallback
        fixed_due_date = (datetime.datetime.now() + datetime.timedelta(days=10)).strftime('%d/%m/%Y')

    # Create the Single PDF Canvas
    c = canvas.Canvas(output_path, pagesize=landscape(A4))
    PAGE_W, PAGE_H = landscape(A4)
    MARGIN = 10 * mm
    COLUMN_GAP = 6 * mm
    COLUMN_WIDTH = (PAGE_W - 2 * MARGIN - 2 * COLUMN_GAP) / 3
    y_top = PAGE_H - MARGIN

    copy_labels = ['School Copy', 'Bank Copy', 'Student Copy']

    # Loop through all students
    for s in students:
        sid, roll, name, father, class_name, campus, whatsapp, fee_amount, paid, pending, default_fee = s

        # Use default fee if not set or 0, but only if no record exists or fee is 0
        if fee_amount == 0 and default_fee:
            fee_amount = default_fee

        # --- Calculate Balance ---
        # Previous balance (All dues BEFORE the selected month)
        cursor.execute('''SELECT COALESCE(SUM(pending),0) FROM fees
                          WHERE student_id = ? AND (year < ? OR (year = ? AND month < ?))''',
                       (sid, year, year, cur_month_num))
        prev_balance = cursor.fetchone()[0] or 0

        # Current month details
        current_month_fee = fee_amount

        # If record exists (pending comes from DB), use it.
        # If record doesn't exist (LEFT JOIN null), assume full fee is pending.
        if pending == 0 and paid == 0:
            # Logic: If nothing paid/recorded, full amount is pending for this month
            current_pending_calc = current_month_fee
        else:
            current_pending_calc = pending

        # Final Payable Calculation
        # Payable = Previous Dues + Current Month Fee (regardless of partial payment, challan usually shows total due)
        # However, typically Challan Payable = Previous Pending + (Current Fee - Paid)
        # Simplified here: Payable = Previous Pending + Current Month Fee (standard for new month issue)

        if (prev_balance + current_month_fee) <= 0:
            particulars = [('No Remaining Dues', 0)]
            payable = 0
        else:
            particulars = [
                ('Previous Balance', prev_balance),
                ('Admission Fee', 0), ('Exam Fee', 0), ('Security', 0),
                ('Monthly Fee', current_month_fee),
                ('Computer Lab', 0), ('Science Lab Fee', 0),
                ('Late Payment Surcharge', 0), ('Concession', 0),
            ]
            payable = prev_balance + current_month_fee

        # Prepare Data Dict
        data = {
            'campus': campus,
            'school': "Usman's Kindergarten High School Sargodha",
            'issue_date': datetime.datetime.now().strftime('%d/%m/%Y'),  # Issue date is always TODAY (printing date)
            'fee_month': month_name[:3].upper(),  # Month is Selected Month
            'Roll': roll,
            'Name': name,
            'Father': father,
            'Class': class_name,
            'particulars': particulars,
            'payable': str(payable),
            'due_date': fixed_due_date  # 10th of Selected Month
        }

        # Draw 3 Copies on the current page
        for i in range(3):
            x = MARGIN + i * (COLUMN_WIDTH + COLUMN_GAP)
            box_y = 14 * mm
            c.rect(x, box_y, COLUMN_WIDTH, 18, stroke=1, fill=0)
            c.setFont('Helvetica-Bold', 9)
            c.drawCentredString(x + COLUMN_WIDTH / 2, box_y + 9, copy_labels[i])
            draw_single_challan_column(c, x, y_top, COLUMN_WIDTH, data)

        # End the page for this student
        c.showPage()

    conn.close()

    # Save the entire file (all pages)
    c.save()


# ==================== UI TAB ====================
class ChallanTab(QWidget):
    def __init__(self, current_user, emitter=None):
        super().__init__()
        self.current_user = current_user
        self.emitter = emitter
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # --- Filter Layout (Campus, Class) ---
        filter_layout = QHBoxLayout()
        self.campus_combo = QComboBox()
        self.class_combo = QComboBox()
        self.campus_combo.addItem("Select Campus", None)
        self.class_combo.addItem("Select Class", None)

        campuses = get_campuses()
        for cid, name in campuses:
            self.campus_combo.addItem(name, cid)
        self.campus_combo.currentIndexChanged.connect(self.on_campus_changed)

        filter_layout.addWidget(QLabel("Campus:"))
        filter_layout.addWidget(self.campus_combo)
        filter_layout.addWidget(QLabel("Class:"))
        filter_layout.addWidget(self.class_combo)

        # --- Date Selection Layout (Month, Year) ---
        date_layout = QHBoxLayout()

        self.month_combo = QComboBox()
        self.year_combo = QComboBox()

        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        self.month_combo.addItems(months)

        # Set default to current month
        current_month_index = datetime.datetime.now().month - 1
        self.month_combo.setCurrentIndex(current_month_index)

        # Populate Years (Current Year - 1 to Current Year + 5)
        current_year = datetime.datetime.now().year
        for y in range(current_year - 1, current_year + 5):
            self.year_combo.addItem(str(y))

        # Set default to current year
        self.year_combo.setCurrentText(str(current_year))

        date_layout.addWidget(QLabel("For Month:"))
        date_layout.addWidget(self.month_combo)
        date_layout.addWidget(QLabel("Year:"))
        date_layout.addWidget(self.year_combo)

        # --- Print Button ---
        print_btn = QPushButton("Print Challans (Single PDF)")
        print_btn.clicked.connect(self.on_print_challans)

        # Add layouts to main layout
        layout.addLayout(filter_layout)
        layout.addLayout(date_layout)
        layout.addWidget(print_btn)

        self.setLayout(layout)

        if self.emitter:
            self.emitter.data_changed.connect(self.reload_data)

        # Load CSS
        css_path = os.path.join(os.path.dirname(__file__), 'styles.css')
        if os.path.exists(css_path):
            with open(css_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())

    def on_campus_changed(self, index):
        self.class_combo.clear()
        self.class_combo.addItem("Select Class", None)
        campus_id = self.campus_combo.currentData()
        if campus_id:
            classes = get_classes(campus_id)
            for cid, name, _ in classes:
                self.class_combo.addItem(name, cid)

    def on_print_challans(self):
        campus_id = self.campus_combo.currentData()
        class_id = self.class_combo.currentData()

        if not campus_id or not class_id:
            QMessageBox.warning(self, "Error", "Please select both campus and class")
            return

        # 1. Get Names for filename (Remove spaces to make it clean)
        campus_name = self.campus_combo.currentText().replace(" ", "_")
        class_name = self.class_combo.currentText().replace(" ", "_")

        # 2. Get Date Info
        selected_month = self.month_combo.currentText()
        selected_year = int(self.year_combo.currentText())

        # 3. Create Unique ID (Current Time: YYYYMMDD_HHMMSS)
        unique_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # 4. Ask User for Base Directory (e.g., Desktop)
        base_dir = QFileDialog.getExistingDirectory(self, "Select Folder to Save Challans")

        if not base_dir:
            return  # User canceled

        try:
            # 5. Create a NEW FOLDER inside the selected directory
            # Folder Name Example: Challans_February_2026_20260119_234510
            folder_name = f"Challans_{selected_month}_{selected_year}_{unique_id}"
            output_folder = os.path.join(base_dir, folder_name)
            os.makedirs(output_folder, exist_ok=True)

            # 6. Create Unique Filename
            # File Name Example: 20260119_234510_Main_Campus_Class_1.pdf
            file_name = f"{unique_id}_{campus_name}_{class_name}.pdf"
            full_file_path = os.path.join(output_folder, file_name)

            # 7. Generate PDF
            generate_class_challans_single_file(full_file_path, class_id, selected_year, selected_month)

            # Success Message
            QMessageBox.information(self, "Success",
                                    f"Saved successfully in new folder:\n\nFolder: {folder_name}\nFile: {file_name}")

            # Optional: Open the folder automatically for user convenience
            try:
                os.startfile(output_folder)
            except:
                pass

        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to generate challans: {str(e)}")

    def reload_data(self):
        # Preserve current selection if possible, or reset
        # Simple reset for data consistency
        self.campus_combo.clear()
        self.campus_combo.addItem("Select Campus", None)
        campuses = get_campuses()
        for cid, name in campuses:
            self.campus_combo.addItem(name, cid)
        self.class_combo.clear()
        self.class_combo.addItem("Select Class", None)