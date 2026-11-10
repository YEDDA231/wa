import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).with_name("clinic.db")


def get_connection():
    # timeout gives SQLite some time to wait for a lock instead of failing immediately
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they do not exist."""
    conn = get_connection()
    cur = conn.cursor()

    # PetOwner table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS PetOwner (
            petOwnerID TEXT PRIMARY KEY,
            petOwnerFName TEXT NOT NULL,
            petOwnerLName TEXT NOT NULL,
            petOwnerBDate TEXT NOT NULL,
            petOwnerTelNo TEXT NOT NULL,
            is_deleted INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    # Veterinarian table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Veterinarian (
            vetID TEXT PRIMARY KEY,
            vetFName TEXT NOT NULL,
            vetLName TEXT NOT NULL,
            vetAddress TEXT NOT NULL,
            vetSpecial TEXT NOT NULL,
            is_deleted INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    # Pet table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Pet (
            petID TEXT PRIMARY KEY,
            petName TEXT NOT NULL,
            petType TEXT NOT NULL,
            petSex TEXT NOT NULL,
            petBDate TEXT NOT NULL,
            petOwnerID TEXT NOT NULL,
            is_deleted INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (petOwnerID) REFERENCES PetOwner(petOwnerID)
        )
        """
    )

    # Consultation table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Consultation (
            consultID TEXT PRIMARY KEY,
            petID TEXT NOT NULL,
            vetID TEXT NOT NULL,
            consultDate TEXT NOT NULL,
            diagnoses TEXT NOT NULL,
            prescription TEXT NOT NULL,
            is_deleted INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (petID) REFERENCES Pet(petID),
            FOREIGN KEY (vetID) REFERENCES Veterinarian(vetID)
        )
        """
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")

