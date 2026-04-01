import sqlite3

from db import get_connection

def add_campus(name):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO campuses(name) VALUES(?)', (name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def add_class(name, campus_id, default_fee):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO classes(name, campus_id, default_fee) VALUES(?,?,?)', (name, campus_id, default_fee))
    except sqlite3.IntegrityError:
        # update existing
        c.execute('UPDATE classes SET default_fee=? WHERE name=? AND campus_id=?', (default_fee, name, campus_id))
    conn.commit()
    conn.close()

def get_campuses():
    conn = get_connection(); c = conn.cursor()
    c.execute('SELECT id,name FROM campuses ORDER BY name')
    rows = c.fetchall(); conn.close()
    return rows

def get_classes(campus_id=None):
    conn = get_connection(); c = conn.cursor()
    if campus_id:
        c.execute('SELECT id,name,default_fee FROM classes WHERE campus_id=? ORDER BY name', (campus_id,))
    else:
        c.execute('SELECT id,name,default_fee FROM classes ORDER BY name')
    rows = c.fetchall(); conn.close()
    return rows