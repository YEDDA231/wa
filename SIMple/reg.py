"""
Minimal Events Registration — Flask + sqlite3. Run: python reg.py
"""
import os
import sqlite3
from contextlib import contextmanager
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Flask, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = "dev"

_BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(_BASE, "database", "events_registration.db")


def init_db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    conn = sqlite3.connect(DB)
    try:
        conn.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE IF NOT EXISTS Events (
                evCode INTEGER PRIMARY KEY AUTOINCREMENT,
                evName TEXT NOT NULL, evDate TEXT NOT NULL,
                evVenue TEXT NOT NULL, evRFee REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS Participants (
                partID INTEGER PRIMARY KEY AUTOINCREMENT,
                evCode INTEGER NOT NULL, partfName TEXT NOT NULL,
                partlName TEXT NOT NULL, partDRate REAL NOT NULL DEFAULT 0,
                FOREIGN KEY (evCode) REFERENCES Events(evCode));
            CREATE TABLE IF NOT EXISTS Registration (
                regCode INTEGER PRIMARY KEY AUTOINCREMENT,
                partID INTEGER NOT NULL, regDate TEXT NOT NULL,
                regFPaid REAL NOT NULL,
                regPMode TEXT NOT NULL CHECK(regPMode IN ('Card','Cash')),
                FOREIGN KEY (partID) REFERENCES Participants(partID));
            """
        )
        conn.commit()
    finally:
        conn.close()


@contextmanager
def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def num(x, label="Number"):
    if not str(x or "").strip():
        raise ValueError(f"{label} required")
    try:
        return float(Decimal(str(x).strip()))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{label} invalid")


def dt(x, label="Date"):
    if not str(x or "").strip():
        raise ValueError(f"{label} required")
    s = str(x).strip()
    try:
        date.fromisoformat(s)
    except ValueError:
        raise ValueError(f"{label} use YYYY-MM-DD")
    return s


def pid(x):
    if not str(x or "").strip():
        raise ValueError("ID required")
    try:
        return int(str(x).strip())
    except ValueError:
        raise ValueError("ID must be a number") from None


def pm(x):
    m = (x or "").strip()
    if m not in ("Card", "Cash"):
        raise ValueError('Pay mode: Card or Cash')
    return m


_db_ok = False


@app.before_request
def _db_once():
    global _db_ok
    if not _db_ok:
        init_db()
        _db_ok = True


@app.route("/", methods=["GET"])
def home():
    ev_filter = request.args.get("ev")
    edit_ev = request.args.get("edit_ev", type=int)
    edit_p = request.args.get("edit_p", type=int)
    event_edit = None
    part_edit = None

    try:
        with db() as c:
            events = c.execute("SELECT * FROM Events ORDER BY evCode").fetchall()
            participants = c.execute(
                """SELECT p.*, e.evName FROM Participants p
                   JOIN Events e ON p.evCode=e.evCode ORDER BY p.partID"""
            ).fetchall()
            registrations = c.execute(
                """SELECT r.*, p.partfName, p.partlName, e.evName
                   FROM Registration r
                   JOIN Participants p ON r.partID=p.partID
                   JOIN Events e ON p.evCode=e.evCode
                   ORDER BY r.regDate DESC, r.regCode DESC"""
            ).fetchall()
            if edit_ev:
                event_edit = c.execute(
                    "SELECT * FROM Events WHERE evCode=?", (edit_ev,)
                ).fetchone()
            if edit_p:
                part_edit = c.execute(
                    "SELECT * FROM Participants WHERE partID=?", (edit_p,)
                ).fetchone()

            report_ev = None
            report_rows = []
            agg = None
            if ev_filter and str(ev_filter).strip():
                try:
                    ec = int(str(ev_filter).strip())
                except ValueError:
                    flash("Bad event code", "danger")
                    ec = None
                if ec is not None:
                    report_ev = c.execute(
                        "SELECT * FROM Events WHERE evCode=?", (ec,)
                    ).fetchone()
                    if report_ev:
                        report_rows = c.execute(
                            """SELECT r.regDate, r.regFPaid,
                               TRIM(p.partfName||' '||p.partlName) AS fullName
                               FROM Registration r JOIN Participants p ON r.partID=p.partID
                               WHERE p.evCode=? ORDER BY r.regDate DESC""",
                            (ec,),
                        ).fetchall()
                        bf = float(report_ev["evRFee"])
                        ar = c.execute(
                            """SELECT COUNT(*) AS n, COALESCE(SUM(r.regFPaid),0) AS s
                               FROM Registration r JOIN Participants p ON r.partID=p.partID
                               WHERE p.evCode=?""",
                            (ec,),
                        ).fetchone()
                        n, s = int(ar["n"]), float(ar["s"])
                        agg = {"n": n, "sum": s, "disc": n * bf - s, "base": bf}
    except (sqlite3.Error, OSError) as e:
        flash(str(e), "danger")
        events, participants, registrations = [], [], []
        event_edit, part_edit = None, None
        report_ev, report_rows, agg = None, [], None

    return render_template(
        "index.html",
        events=events,
        participants=participants,
        registrations=registrations,
        event_edit=event_edit,
        part_edit=part_edit,
        report_ev=report_ev,
        report_rows=report_rows,
        agg=agg,
        ev_filter=ev_filter or "",
    )


@app.post("/save_event")
def save_event():
    try:
        code = request.form.get("evCode")
        name = (request.form.get("evName") or "").strip()
        venue = (request.form.get("evVenue") or "").strip()
        d = dt(request.form.get("evDate"), "Date")
        fee = num(request.form.get("evRFee"), "Fee")
        if not name or not venue:
            raise ValueError("Name and venue required")
        if fee < 0:
            raise ValueError("Fee can't be negative")
        with db() as c:
            if code:
                c.execute(
                    "UPDATE Events SET evName=?,evDate=?,evVenue=?,evRFee=? WHERE evCode=?",
                    (name, d, venue, fee, int(code)),
                )
                flash("Event updated", "success")
            else:
                c.execute(
                    "INSERT INTO Events (evName,evDate,evVenue,evRFee) VALUES (?,?,?,?)",
                    (name, d, venue, fee),
                )
                flash("Event added", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except (sqlite3.Error, OSError) as e:
        flash(str(e), "danger")
    return redirect(url_for("home"))


@app.post("/delete_event/<int:ev_code>")
def delete_event(ev_code):
    try:
        with db() as c:
            c.execute("DELETE FROM Events WHERE evCode=?", (ev_code,))
    except sqlite3.IntegrityError:
        flash("Can't delete: still used by participants", "danger")
    except (sqlite3.Error, OSError) as e:
        flash(str(e), "danger")
    else:
        flash("Event deleted", "success")
    return redirect(url_for("home"))


@app.post("/save_participant")
def save_participant():
    try:
        pcode = request.form.get("partID")
        ec = pid(request.form.get("evCode"))
        fn = (request.form.get("partfName") or "").strip()
        ln = (request.form.get("partlName") or "").strip()
        dr = num(request.form.get("partDRate"), "Discount")
        if not fn or not ln:
            raise ValueError("Names required")
        if dr < 0:
            raise ValueError("Discount can't be negative")
        with db() as c:
            if not c.execute("SELECT 1 FROM Events WHERE evCode=?", (ec,)).fetchone():
                raise ValueError("Bad event code")
            if pcode:
                c.execute(
                    "UPDATE Participants SET evCode=?,partfName=?,partlName=?,partDRate=? WHERE partID=?",
                    (ec, fn, ln, dr, int(pcode)),
                )
                flash("Participant updated", "success")
            else:
                c.execute(
                    "INSERT INTO Participants (evCode,partfName,partlName,partDRate) VALUES (?,?,?,?)",
                    (ec, fn, ln, dr),
                )
                flash("Participant added", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except (sqlite3.Error, OSError) as e:
        flash(str(e), "danger")
    return redirect(url_for("home"))


@app.post("/delete_participant/<int:part_id>")
def delete_participant(part_id):
    try:
        with db() as c:
            c.execute("DELETE FROM Participants WHERE partID=?", (part_id,))
    except sqlite3.IntegrityError:
        flash("Can't delete: has registrations", "danger")
    except (sqlite3.Error, OSError) as e:
        flash(str(e), "danger")
    else:
        flash("Participant deleted", "success")
    return redirect(url_for("home"))


@app.post("/register")
def register():
    try:
        part_id = pid(request.form.get("partID"))
        rdate = dt(request.form.get("regDate"), "Reg date")
        mode = pm(request.form.get("regPMode"))
        with db() as c:
            row = c.execute(
                """SELECT p.partDRate, e.evRFee FROM Participants p
                   JOIN Events e ON p.evCode=e.evCode WHERE p.partID=?""",
                (part_id,),
            ).fetchone()
            if not row:
                raise ValueError("Participant not found")
            paid = float(row["evRFee"]) - float(row["partDRate"])
            if paid < 0:
                raise ValueError("Discount > fee")
            c.execute(
                "INSERT INTO Registration (partID,regDate,regFPaid,regPMode) VALUES (?,?,?,?)",
                (part_id, rdate, paid, mode),
            )
        flash(f"Registered. Fee paid: {paid:.2f}", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except (sqlite3.Error, OSError) as e:
        flash(str(e), "danger")
    return redirect(url_for("home"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
