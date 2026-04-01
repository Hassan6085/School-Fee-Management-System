from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from db import get_connection

def generate_challan_pdf(output_path, student_info, items):
    """Generates 3-copy individual challan for one student."""
    c = canvas.Canvas(output_path, pagesize=landscape(A4))
    width, height = landscape(A4)
    margin_x = 30
    margin_y = 40
    receipt_width = (width - 4 * margin_x) / 3
    start_y = height - margin_y

    def draw_receipt(x_start, copy_label):
        y = start_y
        c.setFont('Helvetica-Bold', 16)
        c.drawString(x_start, y, 'School Fee Challan')
        c.setFont('Helvetica-Bold', 12)
        c.drawRightString(x_start + receipt_width - 5, y, copy_label)
        y -= 25

        c.setFont('Helvetica', 11)
        for k in ('Roll', 'Name', 'Father', 'Class', 'Campus', 'WhatsApp', 'Year', 'Month'):
            if k in student_info:
                c.drawString(x_start, y, f"{k}: {student_info[k]}")
                y -= 14
        y -= 8

        c.setFont('Helvetica-Bold', 11)
        c.drawString(x_start, y, 'Particulars')
        c.drawString(x_start + 150, y, 'Amount')
        c.drawString(x_start + 220, y, 'Paid')
        c.drawString(x_start + 290, y, 'Pending')
        y -= 14

        c.setFont('Helvetica', 10)
        for it in items:
            title = it.get('title', '')
            amt = it.get('amount', 0)
            paid = it.get('paid', 0)
            pending = it.get('pending', 0)
            c.drawString(x_start, y, title)
            c.drawRightString(x_start + 150, y, str(amt))
            c.drawRightString(x_start + 220, y, str(paid))
            c.drawRightString(x_start + 290, y, str(pending))
            y -= 14

        y -= 20
        c.setFont('Helvetica', 10)
        c.drawString(x_start, y, "Note: Please submit payment at school office before due date.")
        c.line(x_start + receipt_width, start_y, x_start + receipt_width, y - 10)

    labels = ['School Copy', 'Bank Copy', 'Student Copy']
    for i, label in enumerate(labels):
        x_pos = margin_x + i * (receipt_width + margin_x)
        draw_receipt(x_pos, label)

    c.showPage()
    c.save()

def generate_class_challans_pdf(output_path, class_id, year, month):
    """Generates challans for all students of a class in one PDF."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''SELECT s.id, s.roll, s.name, s.father, c.name, s.campus, s.whatsapp, f.fee_amount, f.paid, f.pending
                 FROM students s
                 JOIN fees f ON s.id = f.student_id
                 JOIN classes c ON s.class_id = c.id
                 WHERE s.class_id=? AND f.year=? AND f.month=?
                 ORDER BY s.roll''', (class_id, year, month))
    students = c.fetchall()
    conn.close()

    pdf = canvas.Canvas(output_path, pagesize=landscape(A4))
    width, height = landscape(A4)
    margin_x = 30
    margin_y = 40
    receipt_width = (width - 4 * margin_x) / 3
    start_y = height - margin_y

    for s in students:
        sid, roll, name, father, class_name, campus, whatsapp, fee_amount, paid, pending = s
        student_info = {
            'Roll': roll,
            'Name': name,
            'Father': father,
            'Class': class_name,
            'Campus': campus,
            'WhatsApp': whatsapp,
            'Year': year,
            'Month': month
        }
        items = [{
            'title': f'Tuition Fee {month}/{year}',
            'amount': fee_amount,
            'paid': paid,
            'pending': pending
        }]

        def draw_receipt(x_start, copy_label):
            y = start_y
            c.setFont('Helvetica-Bold', 16)
            c.drawString(x_start, y, 'School Fee Challan')
            c.setFont('Helvetica-Bold', 12)
            c.drawRightString(x_start + receipt_width - 5, y, copy_label)
            y -= 25

            c.setFont('Helvetica', 11)
            for k in ('Roll', 'Name', 'Father', 'Class', 'Campus', 'WhatsApp', 'Year', 'Month'):
                if k in student_info:
                    c.drawString(x_start, y, f"{k}: {student_info[k]}")
                    y -= 14
            y -= 8

            c.setFont('Helvetica-Bold', 11)
            c.drawString(x_start, y, 'Particulars')
            c.drawString(x_start + 150, y, 'Amount')
            c.drawString(x_start + 220, y, 'Paid')
            c.drawString(x_start + 290, y, 'Pending')
            y -= 14

            c.setFont('Helvetica', 10)
            for it in items:
                title = it.get('title', '')
                amt = it.get('amount', 0)
                paid_amt = it.get('paid', 0)
                pending_amt = it.get('pending', 0)
                c.drawString(x_start, y, title)
                c.drawRightString(x_start + 150, y, str(amt))
                c.drawRightString(x_start + 220, y, str(paid_amt))
                c.drawRightString(x_start + 290, y, str(pending_amt))
                y -= 14

            y -= 20
            c.setFont('Helvetica', 10)
            c.drawString(x_start, y, "Note: Please submit payment at school office before due date.")
            c.line(x_start + receipt_width, start_y, x_start + receipt_width, y - 10)

        labels = ['School Copy', 'Bank Copy', 'Student Copy']
        for i, label in enumerate(labels):
            x_pos = margin_x + i * (receipt_width + margin_x)
            draw_receipt(x_pos, label)

        pdf.showPage()

    pdf.save()