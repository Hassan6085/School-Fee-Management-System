import datetime
import sqlite3
from db import get_connection
from backend.student_operations import get_students


# --- Setup Transaction Table (Auto-run) ---
def ensure_transaction_table():
    """Creates the fee_transactions table if it doesn't exist."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS fee_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fee_id INTEGER,
                    student_id INTEGER,
                    amount INTEGER,
                    transaction_date TIMESTAMP,
                    FOREIGN KEY(fee_id) REFERENCES fees(id),
                    FOREIGN KEY(student_id) REFERENCES students(id)
                )''')
    conn.commit()
    conn.close()


# Ensure table exists when module loads
ensure_transaction_table()


def generate_monthly_fees(year, month, include_last_month=False):
    """
    Generate monthly fee records for all students.
    """
    if not (isinstance(year, int) and 2000 <= year <= 2100) or not (isinstance(month, int) and 1 <= month <= 12):
        raise ValueError("Invalid year or month value")

    conn = get_connection()
    c = conn.cursor()
    try:
        students = get_students()
        created = 0

        months_to_generate = [month]
        if include_last_month:
            prev_month = month - 1 if month > 1 else 12
            prev_year = year if month > 1 else year - 1
            months_to_generate.insert(0, (prev_month, prev_year))
        else:
            months_to_generate = [(month, year)]

        for s in students:
            sid = s[0]
            class_id = s[4]
            discount_type = s[7] or 'none'
            discount_value = int(s[8] or 0)

            c.execute('SELECT default_fee FROM classes WHERE id=?', (class_id,))
            row = c.fetchone()
            base_fee = int(row[0]) if row else 0

            if discount_type == 'amount':
                discount_applied = discount_value
                fee_amount = max(0, base_fee - discount_value)
            elif discount_type == 'percent':
                discount_applied = base_fee * discount_value // 100
                fee_amount = max(0, base_fee - discount_applied)
            else:
                discount_applied = 0
                fee_amount = base_fee

            for m, y in months_to_generate:
                c.execute('SELECT id FROM fees WHERE student_id=? AND year=? AND month=?', (sid, y, m))
                if c.fetchone():
                    continue

                pending = fee_amount
                issue_date = datetime.datetime.now().strftime("%Y-%m-%d")
                due_date = (datetime.datetime.now() + datetime.timedelta(days=10)).strftime("%Y-%m-%d")

                c.execute('''INSERT INTO fees(
                    student_id, year, month, fee_amount, discount, paid, pending, discount_type,
                    note, created_at, issue_date, due_date
                ) VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?)''', (
                    sid, y, m, fee_amount, discount_applied, pending, discount_type,
                    "Monthly Fee", datetime.datetime.now().isoformat(), issue_date, due_date
                ))
                created += 1

        conn.commit()
        return created

    except Exception as e:
        conn.rollback()
        raise Exception(f"Failed to generate monthly fees: {str(e)}")
    finally:
        conn.close()


def add_payment(fee_id, amount, one_time_discount=0):
    """
    Apply payment to fee record AND log the transaction.
    """
    if not isinstance(amount, (int, float)) or amount < 0:
        raise ValueError("Payment amount must be non-negative")

    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('SELECT student_id, year, month, paid, pending, discount FROM fees WHERE id=?', (fee_id,))
        row = c.fetchone()
        if not row:
            return False

        student_id, year, month, paid, pending, current_discount = row
        paid = int(paid or 0)
        pending = int(pending or 0)
        current_discount = int(current_discount or 0)

        # 1. Apply Runtime Discount
        if one_time_discount > 0:
            actual_discount = min(one_time_discount, pending)
            new_total_discount = current_discount + actual_discount
            pending = pending - actual_discount
            c.execute('UPDATE fees SET discount=?, pending=? WHERE id=?',
                      (new_total_discount, pending, fee_id))

        # 2. Apply Payment
        to_apply = int(amount)
        reduce_here = min(to_apply, pending)
        new_paid = paid + reduce_here
        new_pending = pending - reduce_here
        to_apply -= reduce_here

        # Update Fees Table
        c.execute('UPDATE fees SET paid=?, pending=? WHERE id=?', (new_paid, new_pending, fee_id))

        # LOG TRANSACTION (New Feature)
        if reduce_here > 0:
            c.execute('''INSERT INTO fee_transactions (fee_id, student_id, amount, transaction_date)
                         VALUES (?, ?, ?, ?)''',
                      (fee_id, student_id, reduce_here, datetime.datetime.now()))

        # 3. Carry Over Logic
        carry = to_apply
        if carry > 0:
            c.execute('''SELECT id, pending FROM fees
                         WHERE student_id=? AND (year > ? OR (year = ? AND month > ?))
                         ORDER BY year, month''', (student_id, year, year, month))
            for fid, f_pending in c.fetchall():
                if carry <= 0:
                    break
                used = min(carry, f_pending)
                if used > 0:
                    c.execute('UPDATE fees SET paid=paid+?, pending=? WHERE id=?', (used, f_pending - used, fid))
                    # Log carry-over transaction
                    c.execute('''INSERT INTO fee_transactions (fee_id, student_id, amount, transaction_date)
                                 VALUES (?, ?, ?, ?)''',
                              (fid, student_id, used, datetime.datetime.now()))
                    carry -= used

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise Exception(f"Failed to apply payment: {str(e)}")
    finally:
        conn.close()


def mark_fee_unpaid(fee_id):
    """
    Reverts a paid fee back to unpaid state and removes transaction logs for this fee.
    """
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('SELECT paid, pending, fee_amount FROM fees WHERE id=?', (fee_id,))
        row = c.fetchone()
        if not row:
            return False

        paid, pending, fee_amount = row
        paid = int(paid or 0)

        if paid == 0:
            return True

        # Restore pending
        new_pending = pending + paid
        c.execute('UPDATE fees SET paid=0, pending=? WHERE id=?', (new_pending, fee_id))

        # Remove logs for this fee to keep "Daily Paid" accurate
        c.execute('DELETE FROM fee_transactions WHERE fee_id=?', (fee_id,))

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise Exception(f"Failed to revert payment: {str(e)}")
    finally:
        conn.close()


def get_fees_with_students(filters):
    conn = get_connection()
    c = conn.cursor()
    q = """
        SELECT fees.id, students.roll, students.name, campuses.name, classes.name,
               fees.year, fees.month, fees.fee_amount, 
               fees.discount, fees.paid, fees.pending, fees.discount_type,
               fees.issue_date, fees.due_date
        FROM fees
        JOIN students ON students.id = fees.student_id
        JOIN campuses ON campuses.id = students.campus_id
        JOIN classes ON classes.id = students.class_id
        WHERE 1=1
    """
    params = []
    if "roll" in filters and filters["roll"]:
        q += " AND students.roll LIKE ?"
        params.append(f"%{filters['roll']}%")
    if "name" in filters and filters["name"]:
        q += " AND students.name LIKE ?"
        params.append(f"%{filters['name']}%")
    if "campus_id" in filters and filters["campus_id"]:
        q += " AND students.campus_id=?"
        params.append(filters["campus_id"])
    if "class_id" in filters and filters["class_id"]:
        q += " AND students.class_id=?"
        params.append(filters["class_id"])

    q += " ORDER BY fees.year DESC, fees.month DESC"
    try:
        c.execute(q, params)
        return c.fetchall()
    except Exception as e:
        raise Exception(f"Failed to fetch fees: {str(e)}")
    finally:
        conn.close()


def get_defaulters(**filters):
    conn = get_connection()
    c = conn.cursor()
    try:
        q = '''SELECT f.id, s.roll, s.name, s.whatsapp, c.name, cp.name,
                      f.year, f.month, f.pending
               FROM fees f 
               JOIN students s ON f.student_id=s.id
               JOIN classes c ON c.id = s.class_id
               JOIN campuses cp ON cp.id = s.campus_id
               WHERE f.pending > 0'''
        params = []
        if 'campus_id' in filters and filters['campus_id']:
            q += " AND s.campus_id = ?"
            params.append(filters['campus_id'])
        if 'class_id' in filters and filters['class_id']:
            q += " AND s.class_id = ?"
            params.append(filters['class_id'])
        q += " ORDER BY f.year, f.month"
        c.execute(q, params)
        return c.fetchall()
    except Exception as e:
        raise Exception(f"Failed to fetch defaulters: {str(e)}")
    finally:
        conn.close()


def ensure_fees_for_class(class_id, year, month_name):
    try:
        month_num = datetime.datetime.strptime(month_name, "%B").month
    except Exception:
        raise ValueError(f"Invalid month name: {month_name}")

    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT id FROM students WHERE class_id=?", (class_id,))
        students = c.fetchall()
        created = 0
        for (sid,) in students:
            c.execute("SELECT id FROM fees WHERE student_id=? AND year=? AND month=?", (sid, year, month_num))
            if c.fetchone():
                continue
            c.execute("SELECT default_fee FROM classes WHERE id=?", (class_id,))
            row = c.fetchone()
            base_fee = int(row[0]) if row else 0
            pending = base_fee
            issue_date = datetime.datetime.now().strftime("%Y-%m-%d")
            due_date = (datetime.datetime.now() + datetime.timedelta(days=10)).strftime("%Y-%m-%d")
            c.execute('''INSERT INTO fees(student_id, year, month, fee_amount, discount, paid, pending, discount_type, created_at, issue_date, due_date)
                         VALUES(?,?,?,?,?,?,?,?,?,?,?)''',
                      (sid, year, month_num, base_fee, 0, 0, pending, "none",
                       datetime.datetime.now().isoformat(), issue_date, due_date))
            created += 1
        conn.commit()
        return created
    except Exception as e:
        conn.rollback()
        raise Exception(f"Failed to ensure fees for class: {str(e)}")
    finally:
        conn.close()


def add_event_fee(student_id, event_name, amount):
    if not isinstance(amount, (int, float)) or amount < 0:
        raise ValueError("Fee amount must be non-negative")
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(
            'INSERT INTO event_fees(student_id, event_name, amount, paid, pending, created_at) VALUES(?,?,?,?,?,?)',
            (student_id, event_name, amount, 0, amount, datetime.datetime.now().isoformat()))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise Exception(f"Failed to add event fee: {str(e)}")
    finally:
        conn.close()


def add_historical_fee(student_id, year, month, amount):
    if not (isinstance(year, int) and 2000 <= year <= 2100) or not (isinstance(month, int) and 1 <= month <= 12):
        raise ValueError("Invalid year or month value")
    if not isinstance(amount, (int, float)) or amount < 0:
        raise ValueError("Amount must be a non-negative number")
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('SELECT id FROM fees WHERE student_id = ? AND year = ? AND month = ?', (student_id, year, month))
        if c.fetchone():
            raise ValueError(f"Fee for {datetime.datetime(year, month, 1).strftime('%B %Y')} already exists")
        issue_date = datetime.datetime(year, month, 1).strftime("%Y-%m-%d")
        due_date = (datetime.datetime(year, month, 1) + datetime.timedelta(days=10)).strftime("%Y-%m-%d")
        c.execute('''INSERT INTO fees (
            student_id, year, month, fee_amount, discount, paid, pending, discount_type,
            note, created_at, issue_date, due_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (student_id, year, month, amount, 0, 0, amount, "none",
                   "Historical Fee", datetime.datetime.now().isoformat(), issue_date, due_date))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise Exception(f"Failed to add historical fee: {str(e)}")
    finally:
        conn.close()