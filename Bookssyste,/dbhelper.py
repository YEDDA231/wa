import sqlite3

DB_NAME = "books.db"


def connect():
    return sqlite3.connect(DB_NAME)


def create_table():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        isbn INTEGER PRIMARY KEY,
        title TEXT,
        copyright TEXT,
        edition TEXT,
        price REAL,
        quantity INTEGER
    )
    """)

    conn.commit()
    conn.close()


# ADD
def add_book(isbn, title, copyright, edition, price, quantity):
    conn = connect()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        INSERT INTO books VALUES (?, ?, ?, ?, ?, ?)
        """, (int(isbn), title, copyright, edition, float(price), int(quantity)))

        conn.commit()
        return "Book added successfully"

    except:
        return "ISBN already exists"

    finally:
        conn.close()


# SEARCH
def get_book(isbn):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM books WHERE isbn=?", (isbn,))
    data = cursor.fetchone()

    conn.close()
    return data


# GET ALL + TOTAL (✅ FIXED ERROR HERE)
def get_all():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM books")
    rows = cursor.fetchall()

    # ✅ convert types before math
    total = sum(float(r[4]) * int(r[5]) for r in rows)

    conn.close()
    return rows, total


# UPDATE
def update_book(isbn, title, copyright, edition, price, quantity):
    # validate
    if not title or not copyright or not edition or not price or not quantity:
        return "All fields are required"

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE books
    SET title=?, copyright=?, edition=?, price=?, quantity=?
    WHERE isbn=?
    """, (
        title,
        copyright,
        edition,
        float(price),
        int(quantity),
        int(isbn)
    ))

    conn.commit()
    conn.close()

    return "Book updated successfully"


# DELETE
def delete_book(isbn):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM books WHERE isbn=?", (isbn,))

    conn.commit()
    conn.close()

    return "Book deleted"


# SEED DATA
def seed_data():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM books")
    count = cursor.fetchone()[0]

    if count == 0:
        books = [
            (1, "Harry Potter", "2005", "1st", 595.00, 3),
            (2, "Lord of the Rings", "2004", "3rd", 999.00, 10),
            (3, "Java Programming", "2010", "UPE", 549.00, 2),
            (4, "The Notebook", "1999", "US", 750.00, 11)
        ]

        cursor.executemany("INSERT INTO books VALUES (?, ?, ?, ?, ?, ?)", books)
        conn.commit()

    conn.close()