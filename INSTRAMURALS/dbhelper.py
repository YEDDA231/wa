"""SQLite access for the UC Main Intramurals system.

The table and column names follow the handout. All database work stays in
this file so main.py only handles the Flask menu and forms.
"""

import os
import re
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.environ.get("INTRAMURALS_DB", os.path.join(BASE_DIR, "intramurals.db"))

ROLES = ("admin", "athlete", "tournament manager", "coach", "dean")
ROLE_LABELS = {
    "admin": "Admin",
    "athlete": "Student / Athlete",
    "coach": "Coach",
    "tournament manager": "Tournament Manager",
    "dean": "Dean",
}
REGISTER_ROLES = [(role, ROLE_LABELS[role]) for role in ROLES]
STAFF_TABLE = {
    "tournament manager": "TournamentManager",
    "coach": "Coach",
    "dean": "Dean",
}
CATEGORIES = ("Athletic", "Cultural", "Academic")
YEARS = ("1st Year", "2nd Year", "3rd Year", "4th Year", "5th Year")
CIVIL_STATUSES = ("Single", "Married", "Widowed", "Separated")
GENDERS = ("Male", "Female")

LOCAL_ADMIN_ID = "ADMIN001"
LOCAL_ADMIN_PASSWORD = "Admin@123"

SCHEMA = """
CREATE TABLE IF NOT EXISTS Registration (
    userName TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    confirmPassword TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'athlete', 'tournament manager', 'coach', 'dean'))
);

CREATE TABLE IF NOT EXISTS Department (
    deptID TEXT PRIMARY KEY,
    deptName TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS TournamentManager (
    userName TEXT PRIMARY KEY,
    fName TEXT NOT NULL,
    lName TEXT NOT NULL,
    mobile TEXT NOT NULL,
    deptID TEXT NOT NULL,
    FOREIGN KEY (userName) REFERENCES Registration (userName),
    FOREIGN KEY (deptID) REFERENCES Department (deptID)
);

CREATE TABLE IF NOT EXISTS Coach (
    userName TEXT PRIMARY KEY,
    fName TEXT NOT NULL,
    lName TEXT NOT NULL,
    mobile TEXT NOT NULL,
    deptID TEXT NOT NULL,
    FOREIGN KEY (userName) REFERENCES Registration (userName),
    FOREIGN KEY (deptID) REFERENCES Department (deptID)
);

CREATE TABLE IF NOT EXISTS Dean (
    userName TEXT PRIMARY KEY,
    fName TEXT NOT NULL,
    lName TEXT NOT NULL,
    mobile TEXT NOT NULL,
    deptID TEXT NOT NULL,
    FOREIGN KEY (userName) REFERENCES Registration (userName),
    FOREIGN KEY (deptID) REFERENCES Department (deptID)
);

CREATE TABLE IF NOT EXISTS Event (
    eventID INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL CHECK (category IN ('Athletic', 'Cultural', 'Academic')),
    eventName TEXT NOT NULL,
    noOfParticipant INTEGER NOT NULL CHECK (noOfParticipant > 0),
    tournamentManager TEXT NOT NULL,
    FOREIGN KEY (tournamentManager) REFERENCES TournamentManager (userName)
);

CREATE TABLE IF NOT EXISTS AthletesProfile (
    idNum TEXT PRIMARY KEY,
    eventID INTEGER NOT NULL,
    deptID TEXT NOT NULL,
    lastName TEXT NOT NULL,
    firstName TEXT NOT NULL,
    middleInit TEXT,
    course TEXT NOT NULL,
    year TEXT NOT NULL,
    civilStatus TEXT NOT NULL,
    gender TEXT NOT NULL,
    birthdate TEXT NOT NULL,
    contactNo TEXT NOT NULL,
    address TEXT NOT NULL,
    coachID TEXT NOT NULL,
    deanID TEXT NOT NULL,
    FOREIGN KEY (idNum) REFERENCES Registration (userName),
    FOREIGN KEY (eventID) REFERENCES Event (eventID),
    FOREIGN KEY (deptID) REFERENCES Department (deptID),
    FOREIGN KEY (coachID) REFERENCES Coach (userName),
    FOREIGN KEY (deanID) REFERENCES Dean (userName)
);
"""

EVENT_SQL = """
SELECT
    e.eventID,
    e.category,
    e.eventName,
    e.noOfParticipant,
    e.tournamentManager,
    t.fName AS managerFirst,
    t.lName AS managerLast,
    t.deptID AS managerDeptID,
    d.deptName AS managerDeptName,
    (SELECT COUNT(*) FROM AthletesProfile a WHERE a.eventID = e.eventID) AS joined
FROM Event e
JOIN TournamentManager t ON t.userName = e.tournamentManager
LEFT JOIN Department d ON d.deptID = t.deptID
"""

ATHLETE_SQL = """
SELECT
    a.idNum,
    a.eventID,
    a.deptID,
    a.lastName,
    a.firstName,
    a.middleInit,
    a.course,
    a.year,
    a.civilStatus,
    a.gender,
    a.birthdate,
    a.contactNo,
    a.address,
    a.coachID,
    a.deanID,
    e.eventName,
    e.category,
    e.tournamentManager,
    d.deptName,
    c.fName || ' ' || c.lName AS coachName,
    dn.fName || ' ' || dn.lName AS deanName
FROM AthletesProfile a
JOIN Event e ON e.eventID = a.eventID
JOIN Department d ON d.deptID = a.deptID
JOIN Coach c ON c.userName = a.coachID
JOIN Dean dn ON dn.userName = a.deanID
"""


def _clean(value):
    return (value or "").strip()


class DBHelper:
    def __init__(self, dbname=None):
        self.dbname = dbname or DEFAULT_DB
        self.create_tables()
        self.seed_admin()

    def _connect(self):
        conn = sqlite3.connect(self.dbname, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def query(self, sql, params=()):
        conn = self._connect()
        try:
            return conn.execute(sql, params).fetchall()
        finally:
            conn.close()

    def execute(self, sql, params=(), commit=False):
        conn = self._connect()
        try:
            cur = conn.execute(sql, params)
            rows = cur.fetchall()
            lastrowid = cur.lastrowid
            rowcount = cur.rowcount
            if commit:
                conn.commit()
            return rows, lastrowid, rowcount
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def create_tables(self):
        conn = self._connect()
        try:
            conn.executescript(SCHEMA)
            conn.commit()
        finally:
            conn.close()

    def seed_admin(self):
        if self.get_user(LOCAL_ADMIN_ID):
            return
        self.execute(
            """
            INSERT INTO Registration (userName, password, confirmPassword, role)
            VALUES (?, ?, ?, ?)
            """,
            (LOCAL_ADMIN_ID, LOCAL_ADMIN_PASSWORD, LOCAL_ADMIN_PASSWORD, "admin"),
            commit=True,
        )

    def get_user(self, username):
        rows = self.query(
            "SELECT userName, password, confirmPassword, role FROM Registration WHERE userName = ?",
            (_clean(username).upper(),),
        )
        return rows[0] if rows else None

    def get_users(self):
        return self.query("SELECT userName, role FROM Registration ORDER BY role, userName")

    def authenticate(self, username, password):
        user = self.get_user(username)
        if not user or user["password"] != (password or ""):
            return None
        return user

    def register_user(self, username, password, confirm, role, dept_id=None, f_name=None, l_name=None, mobile=None):
        username = _clean(username).upper()
        role = _clean(role).lower()
        error = self._validate_registration(username, password, confirm, role)
        if error:
            return False, error
        table = STAFF_TABLE.get(role)
        if table:
            dept_id = _clean(dept_id).upper()
            f_name = _clean(f_name)
            l_name = _clean(l_name)
            mobile = _clean(mobile)
            if not dept_id or not self.get_department(dept_id):
                return False, "Choose the department this person belongs to."
            if not f_name or not l_name or not mobile:
                return False, "Enter the first name, last name, and mobile number."
            if len(f_name) > 50 or len(l_name) > 50 or len(mobile) > 20:
                return False, "Name or mobile number is too long."
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO Registration (userName, password, confirmPassword, role)
                VALUES (?, ?, ?, ?)
                """,
                (username, password, confirm, role),
            )
            if table:
                conn.execute(
                    f"""
                    INSERT INTO {table} (userName, fName, lName, mobile, deptID)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (username, f_name, l_name, mobile, dept_id),
                )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.rollback()
            return False, "That ID number is already registered."
        finally:
            conn.close()
        if table:
            return True, f"Registration saved in {dept_id}. They can log in with that ID number."
        return True, "Registration saved. You can log in with that ID number."

    def _validate_registration(self, username, password, confirm, role):
        if not username:
            return "ID number is required."
        if not re.fullmatch(r"[A-Z0-9\-]+", username):
            return "ID number may use letters, numbers, and hyphens only."
        if role not in ROLES:
            return "Choose a valid role."
        if password != confirm:
            return "Password and confirm password do not match."
        has_letter = re.search(r"[A-Za-z]", password or "")
        has_digit = re.search(r"\d", password or "")
        has_special = re.search(r"[^A-Za-z0-9]", password or "")
        if not (has_letter and has_digit and has_special):
            return "Password must be made up of letters, numbers, and special characters."
        return None

    def get_departments(self):
        return self.query("SELECT deptID, deptName FROM Department ORDER BY deptID")

    def get_department(self, dept_id):
        rows = self.query(
            "SELECT deptID, deptName FROM Department WHERE deptID = ?",
            (_clean(dept_id).upper(),),
        )
        return rows[0] if rows else None

    def add_department(self, dept_id, dept_name):
        dept_id = _clean(dept_id).upper()
        dept_name = _clean(dept_name)
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9\-]{0,19}", dept_id or ""):
            return False, "Use a short department ID such as CCS or COE."
        if not dept_name or len(dept_name) > 80:
            return False, "Enter a department name (80 characters or fewer)."
        try:
            self.execute(
                "INSERT INTO Department (deptID, deptName) VALUES (?, ?)",
                (dept_id, dept_name),
                commit=True,
            )
        except sqlite3.IntegrityError:
            return False, "That department ID already exists."
        return True, "Department created."

    def rename_department(self, dept_id, dept_name):
        dept_id = _clean(dept_id).upper()
        dept_name = _clean(dept_name)
        if not dept_name or len(dept_name) > 80:
            return False, "Enter a department name (80 characters or fewer)."
        if not self.get_department(dept_id):
            return False, "Department not found."
        self.execute(
            "UPDATE Department SET deptName = ? WHERE deptID = ?",
            (dept_name, dept_id),
            commit=True,
        )
        return True, "Department name updated."

    def get_staff(self, role, username):
        table = STAFF_TABLE.get(role)
        if not table:
            return None
        rows = self.query(
            f"""
            SELECT s.userName, s.fName, s.lName, s.mobile, s.deptID, d.deptName
            FROM {table} s
            JOIN Department d ON d.deptID = s.deptID
            WHERE s.userName = ?
            """,
            (_clean(username).upper(),),
        )
        return rows[0] if rows else None

    def list_staff(self, role):
        table = STAFF_TABLE.get(role)
        if not table:
            return []
        return self.query(
            f"""
            SELECT s.userName, s.fName, s.lName, s.mobile, s.deptID, d.deptName
            FROM {table} s
            JOIN Department d ON d.deptID = s.deptID
            ORDER BY s.lName, s.fName
            """
        )

    def save_staff(self, role, username, f_name, l_name, mobile, dept_id):
        table = STAFF_TABLE.get(role)
        if not table:
            return False, "That role does not use this profile."
        username = _clean(username).upper()
        f_name = _clean(f_name)
        l_name = _clean(l_name)
        mobile = _clean(mobile)
        dept_id = _clean(dept_id).upper()
        if not f_name or not l_name or not mobile or not dept_id:
            return False, "First name, last name, mobile, and department are required."
        if len(f_name) > 50 or len(l_name) > 50:
            return False, "Names must be 50 characters or fewer."
        if len(mobile) > 20:
            return False, "Mobile number is too long."
        if not self.get_department(dept_id):
            return False, "Choose a department that already exists."
        if not self.get_user(username):
            return False, "Register this ID number before saving a profile."
        existing = self.get_staff(role, username)
        if existing and existing["deptID"] != dept_id and role in ("coach", "dean"):
            column = "coachID" if role == "coach" else "deanID"
            used = self.query(
                f"SELECT COUNT(*) AS total FROM AthletesProfile WHERE {column} = ?",
                (username,),
            )
            if used[0]["total"]:
                return False, "Department cannot change while athletes are linked to this profile."
        try:
            if existing:
                self.execute(
                    f"""
                    UPDATE {table}
                    SET fName = ?, lName = ?, mobile = ?, deptID = ?
                    WHERE userName = ?
                    """,
                    (f_name, l_name, mobile, dept_id, username),
                    commit=True,
                )
                return True, "Profile updated."
            self.execute(
                f"""
                INSERT INTO {table} (userName, fName, lName, mobile, deptID)
                VALUES (?, ?, ?, ?, ?)
                """,
                (username, f_name, l_name, mobile, dept_id),
                commit=True,
            )
        except sqlite3.IntegrityError:
            return False, "Could not save the profile. Check the department and account."
        return True, "Profile saved."

    def get_events(self):
        return self.query(EVENT_SQL + " ORDER BY e.eventID")

    def get_event(self, event_id):
        try:
            event_id = int(event_id)
        except (TypeError, ValueError):
            return None
        rows = self.query(EVENT_SQL + " WHERE e.eventID = ?", (event_id,))
        return rows[0] if rows else None

    def count_events_for(self, manager):
        rows = self.query(
            "SELECT COUNT(*) AS total FROM Event WHERE tournamentManager = ?",
            (_clean(manager).upper(),),
        )
        return rows[0]["total"]

    def count_participants(self, event_id, ignore_id=None):
        if ignore_id:
            rows = self.query(
                "SELECT COUNT(*) AS total FROM AthletesProfile WHERE eventID = ? AND idNum != ?",
                (event_id, ignore_id),
            )
        else:
            rows = self.query(
                "SELECT COUNT(*) AS total FROM AthletesProfile WHERE eventID = ?",
                (event_id,),
            )
        return rows[0]["total"]

    def list_athlete_accounts(self, dept_id=None):
        sql = """
            SELECT r.userName,
                   CASE WHEN a.idNum IS NULL THEN 0 ELSE 1 END AS hasProfile,
                   a.deptID
            FROM Registration r
            LEFT JOIN AthletesProfile a ON a.idNum = r.userName
            WHERE r.role = 'athlete'
        """
        params = ()
        if dept_id:
            sql += " AND (a.idNum IS NULL OR a.deptID = ?)"
            params = (_clean(dept_id).upper(),)
        sql += " ORDER BY r.userName"
        return self.query(sql, params)

    def save_event(self, manager, category, event_name, slots, event_id=None, allow_any=False):
        manager = _clean(manager).upper()
        category = _clean(category).title()
        event_name = _clean(event_name)
        if category not in CATEGORIES:
            return False, "Category must be Athletic, Cultural, or Academic."
        if not event_name or len(event_name) > 80:
            return False, "Enter an event name (80 characters or fewer)."
        try:
            slots = int(slots)
        except (TypeError, ValueError):
            return False, "Number of participants must be a whole number."
        if slots < 1 or slots > 500:
            return False, "Number of participants must be from 1 to 500."
        if not self.get_staff("tournament manager", manager):
            if allow_any:
                return False, "Choose a tournament manager who already saved a profile."
            return False, "Save your tournament manager profile before creating an event."
        if event_id not in (None, ""):
            try:
                event_id = int(event_id)
            except (TypeError, ValueError):
                return False, "Event not found."
            event = self.get_event(event_id)
            if not event:
                return False, "Event not found."
            if not allow_any and event["tournamentManager"] != manager:
                return False, "You can only update your own events."
            joined = self.count_participants(event_id)
            if slots < joined:
                return False, f"This event already has {joined} athlete(s). Slots cannot go below that."
            self.execute(
                """
                UPDATE Event
                SET category = ?, eventName = ?, noOfParticipant = ?, tournamentManager = ?
                WHERE eventID = ?
                """,
                (category, event_name, slots, manager, event_id),
                commit=True,
            )
            return True, "Event updated."
        self.execute(
            """
            INSERT INTO Event (category, eventName, noOfParticipant, tournamentManager)
            VALUES (?, ?, ?, ?)
            """,
            (category, event_name, slots, manager),
            commit=True,
        )
        return True, "Event created."

    def get_athlete(self, id_num):
        rows = self.query(ATHLETE_SQL + " WHERE a.idNum = ?", (_clean(id_num).upper(),))
        return rows[0] if rows else None

    def athlete_exists(self, id_num):
        rows = self.query(
            "SELECT idNum FROM AthletesProfile WHERE idNum = ?",
            (_clean(id_num).upper(),),
        )
        return bool(rows)

    def get_athletes(self, coach_id=None, dept_id=None, manager=None):
        sql = ATHLETE_SQL
        clauses = []
        params = []
        if coach_id:
            clauses.append("a.coachID = ?")
            params.append(_clean(coach_id).upper())
        if dept_id:
            clauses.append("a.deptID = ?")
            params.append(_clean(dept_id).upper())
        if manager:
            clauses.append("e.tournamentManager = ?")
            params.append(_clean(manager).upper())
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY a.lastName, a.firstName"
        return self.query(sql, tuple(params))

    def save_athlete(self, id_num, data):
        id_num = _clean(id_num).upper()
        user = self.get_user(id_num)
        if not user or user["role"] != "athlete":
            return False, "Only a registered student can save an athlete profile."

        last_name = _clean(data.get("lastName"))
        first_name = _clean(data.get("firstName"))
        middle = _clean(data.get("middleInit")).upper()
        course = _clean(data.get("course"))
        year = _clean(data.get("year"))
        civil = _clean(data.get("civilStatus"))
        gender = _clean(data.get("gender"))
        birthdate = _clean(data.get("birthdate"))
        contact = _clean(data.get("contactNo"))
        address = _clean(data.get("address"))
        dept_id = _clean(data.get("deptID")).upper()
        coach_id = _clean(data.get("coachID")).upper()
        dean_id = _clean(data.get("deanID")).upper()

        if not all([last_name, first_name, course, year, civil, gender, birthdate, contact, address, dept_id, coach_id, dean_id]):
            return False, "Complete every required field. Middle initial is the only optional one."
        if len(last_name) > 50 or len(first_name) > 50:
            return False, "Names must be 50 characters or fewer."
        if middle and not re.fullmatch(r"[A-Z.]{1,3}", middle):
            return False, "Middle initial should be 1 to 3 letters."
        if len(course) > 40:
            return False, "Course is too long."
        if year not in YEARS:
            return False, "Choose a year level."
        if civil not in CIVIL_STATUSES:
            return False, "Choose a civil status."
        if gender not in GENDERS:
            return False, "Choose a gender."
        if len(contact) > 20:
            return False, "Contact number is too long."
        if len(address) > 200:
            return False, "Address must be 200 characters or fewer."
        try:
            datetime.strptime(birthdate, "%Y-%m-%d")
        except ValueError:
            return False, "Enter a valid birthdate."
        try:
            event_id = int(data.get("eventID"))
        except (TypeError, ValueError):
            return False, "Choose an event."

        event = self.get_event(event_id)
        if not event:
            return False, "That event does not exist."
        if self.count_participants(event_id, ignore_id=id_num) >= event["noOfParticipant"]:
            return False, "That event is already full."
        if not self.get_department(dept_id):
            return False, "Choose a department."
        coach = self.get_staff("coach", coach_id)
        if not coach or coach["deptID"] != dept_id:
            return False, "Choose a coach from the selected department."
        dean = self.get_staff("dean", dean_id)
        if not dean or dean["deptID"] != dept_id:
            return False, "Choose a dean from the selected department."

        params = (
            event_id,
            dept_id,
            last_name,
            first_name,
            middle,
            course,
            year,
            civil,
            gender,
            birthdate,
            contact,
            address,
            coach_id,
            dean_id,
            id_num,
        )
        try:
            if self.athlete_exists(id_num):
                self.execute(
                    """
                    UPDATE AthletesProfile
                    SET eventID = ?, deptID = ?, lastName = ?, firstName = ?, middleInit = ?,
                        course = ?, year = ?, civilStatus = ?, gender = ?, birthdate = ?,
                        contactNo = ?, address = ?, coachID = ?, deanID = ?
                    WHERE idNum = ?
                    """,
                    params,
                    commit=True,
                )
                return True, "Athlete profile updated."
            self.execute(
                """
                INSERT INTO AthletesProfile (
                    eventID, deptID, lastName, firstName, middleInit, course, year,
                    civilStatus, gender, birthdate, contactNo, address, coachID, deanID, idNum
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                params,
                commit=True,
            )
        except sqlite3.IntegrityError:
            return False, "Could not save the athlete profile. Check the event, coach, and dean."
        return True, "Athlete profile saved."

    def counts(self):
        names = {
            "users": "Registration",
            "departments": "Department",
            "managers": "TournamentManager",
            "coaches": "Coach",
            "deans": "Dean",
            "events": "Event",
            "athletes": "AthletesProfile",
        }
        result = {}
        for key, table in names.items():
            rows = self.query(f"SELECT COUNT(*) AS total FROM {table}")
            result[key] = rows[0]["total"]
        return result
