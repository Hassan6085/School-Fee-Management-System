import sqlite3
from db import get_connection, hash_password

def register_user(username, password, full_name, email, role='user'):
    """Register a new user (admin should use this via Add User dialog)."""
    conn = get_connection()
    c = conn.cursor()
    try:
        password_hash = hash_password(password)
        c.execute(
            '''INSERT INTO users(username, password_hash, full_name, email, role)
               VALUES(?, ?, ?, ?, ?)''',
            (username, password_hash, full_name, email, role),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Username already exists
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    """Authenticate a user and return their details dict if valid."""
    conn = get_connection()
    c = conn.cursor()

    password_hash = hash_password(password)
    c.execute(
        '''SELECT id, username, full_name, email, role 
           FROM users WHERE username=? AND password_hash=?''',
        (username, password_hash),
    )

    user = c.fetchone()
    conn.close()

    if user:
        return {
            'id': user[0],
            'username': user[1],
            'full_name': user[2],
            'email': user[3],
            'role': user[4],
        }
    return None

def user_exists(username):
    """Check if a username already exists."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users WHERE username=?', (username,))
    exists = c.fetchone()[0] > 0
    conn.close()
    return exists

def get_all_users():
    """Get all users (admin-only in UI, but returns all rows)."""
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        'SELECT id, username, full_name, email, role, created_at '
        'FROM users ORDER BY username'
    )
    users = c.fetchall()
    conn.close()
    return users

# ------------------------- Admin helper functions -------------------------

def get_user_by_id(user_id):
    """Fetch a single user row by id."""
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        'SELECT id, username, full_name, email, role FROM users WHERE id=?',
        (user_id,),
    )
    row = c.fetchone()
    conn.close()
    if row:
        return {
            'id': row[0],
            'username': row[1],
            'full_name': row[2],
            'email': row[3],
            'role': row[4],
        }
    return None

def is_admin_by_id(user_id):
    """Return True if user_id corresponds to an admin user."""
    user = get_user_by_id(user_id)
    return user and user.get('role') == 'admin'

# ------------------------- Protected admin ops -------------------------

def delete_user_admin(requesting_user_id, user_id_to_delete):
    """Delete a user — only if requester is admin."""
    if not is_admin_by_id(requesting_user_id):
        raise PermissionError("Admin privileges required")
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('DELETE FROM users WHERE id=?', (user_id_to_delete,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def update_user_role_admin(requesting_user_id, user_id_to_update, role):
    """Update user role — only if requester is admin."""
    if not is_admin_by_id(requesting_user_id):
        raise PermissionError("Admin privileges required")
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('UPDATE users SET role=? WHERE id=?', (role, user_id_to_update))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()