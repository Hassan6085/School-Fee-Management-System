import sqlite3
from db import get_connection


# --- Helper function to check if user is admin ---
def is_admin(current_user) -> bool:
    """Check if the logged-in user is an admin/root."""
    return current_user and current_user.get('role') == "admin"


# --- Add student ---
def add_student(current_user, roll, name, father, class_id, campus_id, whatsapp, discount_type='none',
                discount_value=0):
    if not is_admin(current_user):
        raise PermissionError("Only admin can add students!")
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''INSERT INTO students
                     (roll,name,father,class_id,campus_id,whatsapp,discount_type,discount_value)
                     VALUES(?,?,?,?,?,?,?,?)''',
                  (roll, name, father, class_id, campus_id, whatsapp, discount_type, discount_value))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


# --- Get students list (UPDATED) ---
def get_students(name=None, campus_id=None, class_id=None):
    conn = get_connection()
    c = conn.cursor()
    q = '''SELECT id, roll, name, father, class_id, campus_id, whatsapp, discount_type, discount_value 
           FROM students WHERE 1=1'''
    params = []

    # Filter by Name
    if name:
        q += ' AND name LIKE ?'
        params.append(f"%{name}%")

    # Filter by Campus
    if campus_id:
        q += ' AND campus_id=?'
        params.append(campus_id)

    # Filter by Class
    if class_id:
        q += ' AND class_id=?'
        params.append(class_id)

    q += " ORDER BY roll ASC"

    c.execute(q, params)
    rows = c.fetchall()
    conn.close()
    return rows


# --- Get single student details ---
def get_student_details(student_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''SELECT s.id, s.roll, s.name, s.father, c.name, cp.name, s.whatsapp, 
                        s.discount_type, s.discount_value
                 FROM students s
                 JOIN classes c ON s.class_id = c.id
                 JOIN campuses cp ON s.campus_id = cp.id
                 WHERE s.id = ?''', (student_id,))
    row = c.fetchone()
    conn.close()
    return row


# --- Update student ---
def update_student(current_user, student_id, **kwargs):
    if not is_admin(current_user):
        raise PermissionError("Only admin can update students!")
    conn = get_connection()
    c = conn.cursor()
    fields = []
    values = []
    for key, value in kwargs.items():
        fields.append(f"{key}=?")
        values.append(value)
    if not fields:
        return False
    values.append(student_id)
    q = f"UPDATE students SET {', '.join(fields)} WHERE id=?"
    c.execute(q, values)
    conn.commit()
    conn.close()
    return True


# --- Delete student ---
def delete_student(current_user, student_id):
    if not is_admin(current_user):
        raise PermissionError("Only admin can delete students!")
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM students WHERE id=?", (student_id,))
    conn.commit()
    conn.close()
    return True


def get_all_campuses():
    return None


def get_classes_by_campus():
    return None


def get_students_by_class():
    return None