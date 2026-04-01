import sqlite3
import os
import hashlib

DB_FILE = 'school_fees.db'

def get_connection():
    return sqlite3.connect(DB_FILE)

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """Initialize DB and apply light migrations for older schemas."""
    conn = get_connection()
    c = conn.cursor()

    # Users table for authentication
    c.execute('''CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT,
        role TEXT DEFAULT 'user',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # Insert default admin user if not exists
    c.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
    if c.fetchone()[0] == 0:
        admin_password_hash = hash_password('admin')
        c.execute('''INSERT INTO users(username, password_hash, full_name, email, role)
                     VALUES(?, ?, ?, ?, ?)''',
                  ('admin', admin_password_hash, 'Administrator', 'admin@school.com', 'admin'))

    # campuses
    c.execute('''CREATE TABLE IF NOT EXISTS campuses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )''')

    # classes
    c.execute('''CREATE TABLE IF NOT EXISTS classes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        campus_id INTEGER,
        default_fee INTEGER DEFAULT 0,
        FOREIGN KEY(campus_id) REFERENCES campuses(id)
    )''')

    # remove duplicate class entries (keep smallest id), then add unique index
    try:
        c.execute('''
            DELETE FROM classes
            WHERE id NOT IN (
                SELECT MIN(id) FROM classes GROUP BY name, campus_id
            )
        ''')
    except Exception:
        # ignore issues if table empty / unsupported
        pass
    c.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_class_unique ON classes(name, campus_id)')

    # students: include discount fields
    c.execute('''CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll TEXT,
        name TEXT,
        father TEXT,
        class_id INTEGER,
        campus_id INTEGER,
        whatsapp TEXT,
        discount_type TEXT DEFAULT 'none',
        discount_value INTEGER DEFAULT 0,
        UNIQUE(roll, class_id, campus_id),
        FOREIGN KEY(class_id) REFERENCES classes(id),
        FOREIGN KEY(campus_id) REFERENCES campuses(id)
    )''')

    # ensure older DBs get discount columns added if missing
    c.execute("PRAGMA table_info(students)")
    existing_student_cols = [row[1] for row in c.fetchall()]
    if "discount_type" not in existing_student_cols:
        try:
            c.execute("ALTER TABLE students ADD COLUMN discount_type TEXT DEFAULT 'none'")
        except Exception:
            pass
    if "discount_value" not in existing_student_cols:
        try:
            c.execute("ALTER TABLE students ADD COLUMN discount_value INTEGER DEFAULT 0")
        except Exception:
            pass

    # fees: include discount_type, issue_date, and due_date columns
    c.execute('''CREATE TABLE IF NOT EXISTS fees(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        year INTEGER,
        month INTEGER,
        fee_amount INTEGER,
        discount INTEGER DEFAULT 0,
        paid INTEGER DEFAULT 0,
        pending INTEGER DEFAULT 0,
        discount_type TEXT DEFAULT 'none',
        note TEXT,
        created_at TEXT,
        issue_date TEXT,  -- New column for issue date
        due_date TEXT,    -- New column for due date
        FOREIGN KEY(student_id) REFERENCES students(id)
    )''')

    c.execute("PRAGMA table_info(fees)")
    existing_fee_cols = [row[1] for row in c.fetchall()]
    if "discount_type" not in existing_fee_cols:
        try:
            c.execute("ALTER TABLE fees ADD COLUMN discount_type TEXT DEFAULT 'none'")
        except Exception:
            pass
    if "issue_date" not in existing_fee_cols:
        try:
            c.execute("ALTER TABLE fees ADD COLUMN issue_date TEXT")
        except Exception:
            pass
    if "due_date" not in existing_fee_cols:
        try:
            c.execute("ALTER TABLE fees ADD COLUMN due_date TEXT")
        except Exception:
            pass

    # event fees
    c.execute('''CREATE TABLE IF NOT EXISTS event_fees(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        event_name TEXT,
        amount INTEGER,
        paid INTEGER DEFAULT 0,
        pending INTEGER DEFAULT 0,
        created_at TEXT,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )''')

    conn.commit()
    conn.close()