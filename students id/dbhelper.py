import sqlite3
from datetime import datetime

DB_NAME = "students.db"

def connect():
    return sqlite3.connect(DB_NAME)

def create_table():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT UNIQUE,
    name TEXT,
    course TEXT,
    score REAL,
    date_added TEXT
)
""")

    conn.commit()
    conn.close()


# CREATE



# READ
def get_all_students():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students")
    data = cursor.fetchall()

    conn.close()
    return data


# SEARCH
def search_student(keyword):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM students
    WHERE student_id LIKE ? OR name LIKE ?
    """, (f"%{keyword}%", f"%{keyword}%"))

    data = cursor.fetchall()
    conn.close()
    return data


# GET ONE
def get_student(id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE id = ?", (id,))
    data = cursor.fetchone()

    conn.close()
    return data


# UPDATE
def update_student(id, name, course, score):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE students
    SET name = ?, course = ?, score = ?
    WHERE id = ?
    """, (name, course, score, id))

    conn.commit()
    conn.close()


# DELETE
def delete_student(id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM students WHERE id = ?", (id,))

    conn.commit()
    conn.close()

def add_student(student_id, name, course, score):
    conn = connect()
    cursor = conn.cursor()

    date_added = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO students (student_id, name, course, score, date_added)
    VALUES (?, ?, ?, ?, ?)
    """, (student_id, name, course, score, date_added))

    conn.commit()
    conn.close()

