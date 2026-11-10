"""UC Main Intramurals System.

Flask menu and forms. Database work lives in dbhelper.py (sqlite3).
Local admin: ADMIN001 / Admin@123
"""

from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for

from dbhelper import (
    CATEGORIES,
    CIVIL_STATUSES,
    DBHelper,
    GENDERS,
    LOCAL_ADMIN_ID,
    LOCAL_ADMIN_PASSWORD,
    REGISTER_ROLES,
    ROLE_LABELS,
    STAFF_TABLE,
    YEARS,
)

app = Flask(__name__)
app.secret_key = "uc-main-intramurals-local"
db = DBHelper()

PROFILE_TITLES = {
    "coach": "Coach Profile",
    "dean": "Dean Profile",
    "tournament manager": "Tournament Manager",
}
PEOPLE_TITLES = {
    "coach": "Coaches",
    "dean": "Deans",
    "tournament manager": "Tournament Managers",
}
ATHLETE_FIELDS = (
    "eventID",
    "deptID",
    "lastName",
    "firstName",
    "middleInit",
    "course",
    "year",
    "civilStatus",
    "gender",
    "birthdate",
    "contactNo",
    "address",
    "coachID",
    "deanID",
)


def require_login(roles=None):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "userName" not in session:
                flash("Log in to open that page.", "error")
                return redirect(url_for("login"))
            if roles and session.get("role") not in roles:
                flash("Your role cannot open that module.", "error")
                return redirect(url_for(landing_endpoint(session.get("role"))))
            return view(*args, **kwargs)

        return wrapped

    return decorator


def landing_endpoint(role):
    if role == "athlete":
        return "athlete_profile"
    if role in STAFF_TABLE:
        return "profile"
    return "dashboard"


def build_menu():
    role = session.get("role")
    if not role:
        return [
            {"endpoint": "home", "label": "Home"},
            {"endpoint": "home", "label": "Register", "anchor": "register"},
            {"endpoint": "login", "label": "Login"},
        ]
    if role == "admin":
        items = [
            {"endpoint": "dashboard", "label": "Dashboard"},
            {"endpoint": "register", "label": "Register"},
            {"endpoint": "departments", "label": "Departments"},
            {"endpoint": "events", "label": "Events"},
            {"endpoint": "athletes", "label": "Participants"},
            {"endpoint": "users", "label": "Registrations"},
            {"endpoint": "managers", "label": "Tournament Managers"},
            {"endpoint": "coaches", "label": "Coaches"},
            {"endpoint": "deans", "label": "Deans"},
        ]
    elif role == "tournament manager":
        items = [
            {"endpoint": "profile", "label": "My Profile"},
            {"endpoint": "events", "label": "Events"},
            {"endpoint": "athletes", "label": "Participants"},
        ]
    elif role == "coach":
        items = [
            {"endpoint": "profile", "label": "My Profile"},
            {"endpoint": "events", "label": "Events"},
            {"endpoint": "athletes", "label": "Department Students"},
        ]
    elif role == "dean":
        items = [
            {"endpoint": "profile", "label": "My Profile"},
            {"endpoint": "events", "label": "Events"},
            {"endpoint": "athletes", "label": "Participants"},
        ]
    elif role == "athlete":
        items = [
            {"endpoint": "athlete_profile", "label": "My Profile"},
            {"endpoint": "events", "label": "Events"},
        ]
    else:
        items = [{"endpoint": "dashboard", "label": "Dashboard"}]
    items.append({"endpoint": "logout", "label": "Logout"})
    return items


@app.context_processor
def inject_menu():
    return {
        "menu": build_menu(),
        "role_labels": ROLE_LABELS,
        "register_roles": REGISTER_ROLES,
        "categories": CATEGORIES,
        "years": YEARS,
        "civil_statuses": CIVIL_STATUSES,
        "genders": GENDERS,
        "local_admin_id": LOCAL_ADMIN_ID,
        "local_admin_password": LOCAL_ADMIN_PASSWORD,
    }


def render_people(role):
    return render_template(
        "people.html",
        people=db.list_staff(role),
        title=PEOPLE_TITLES[role],
        table_name=STAFF_TABLE[role],
    )


def athlete_form_values(profile, source=None):
    form = {}
    for key in ATHLETE_FIELDS:
        if source is not None:
            value = source.get(key, "")
        elif profile is not None:
            value = profile[key]
            if value is None:
                value = ""
        else:
            value = ""
        if key == "deptID":
            value = str(value).strip().upper()
        form[key] = value
    return form


def profile_payload(athlete, event_id=None):
    data = {}
    for key in ATHLETE_FIELDS:
        value = athlete[key]
        data[key] = "" if value is None else value
    if event_id is not None:
        data["eventID"] = event_id
    return data


@app.route("/", methods=["GET", "POST"])
def home():
    if session.get("userName"):
        return redirect(url_for(landing_endpoint(session["role"])))
    form = {"userName": ""}
    if request.method == "POST":
        form["userName"] = (request.form.get("userName") or "").strip().upper()
        ok, message = db.register_user(
            form["userName"],
            request.form.get("password") or "",
            request.form.get("confirmPassword") or "",
            "athlete",
        )
        flash(message, "success" if ok else "error")
        if ok:
            return redirect(url_for("login"))
    return render_template("home.html", form=form)


@app.route("/register", methods=["GET", "POST"])
@require_login(["admin"])
def register():
    form = {"userName": "", "role": "", "deptID": "", "fName": "", "lName": "", "mobile": ""}
    if request.method == "POST":
        form["userName"] = (request.form.get("userName") or "").strip().upper()
        form["role"] = (request.form.get("role") or "").strip().lower()
        form["deptID"] = (request.form.get("deptID") or "").strip().upper()
        form["fName"] = request.form.get("fName") or ""
        form["lName"] = request.form.get("lName") or ""
        form["mobile"] = request.form.get("mobile") or ""
        ok, message = db.register_user(
            form["userName"],
            request.form.get("password") or "",
            request.form.get("confirmPassword") or "",
            form["role"],
            form["deptID"],
            form["fName"],
            form["lName"],
            form["mobile"],
        )
        flash(message, "success" if ok else "error")
        if ok:
            return redirect(url_for("register"))
    return render_template("register.html", form=form, departments=db.get_departments())


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("userName"):
        return redirect(url_for(landing_endpoint(session["role"])))
    form = {"userName": ""}
    if request.method == "POST":
        form["userName"] = (request.form.get("userName") or "").strip().upper()
        user = db.authenticate(form["userName"], request.form.get("password") or "")
        if not user:
            flash("ID number or password is incorrect.", "error")
        else:
            session.clear()
            session["userName"] = user["userName"]
            session["role"] = user["role"]
            flash("Welcome to UC Main Intramurals.", "success")
            return redirect(url_for(landing_endpoint(user["role"])))
    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@require_login()
def dashboard():
    role = session["role"]
    username = session["userName"]
    profile = None
    if role in STAFF_TABLE:
        profile = db.get_staff(role, username)
    elif role == "athlete":
        profile = db.get_athlete(username)
    counts = db.counts()
    hints = []
    if role == "admin" and counts["departments"] == 0:
        hints.append(
            {
                "text": "Create a department so coaches, deans, and tournament managers can finish their profiles.",
                "href": url_for("departments"),
                "label": "Departments",
            }
        )
    if role in STAFF_TABLE and not profile:
        hints.append(
            {
                "text": "Save your profile. Your ID is already registered; this adds your name, mobile, and department.",
                "href": url_for("profile"),
                "label": "My Profile",
            }
        )
    if role == "tournament manager" and profile and db.count_events_for(username) == 0:
        hints.append(
            {
                "text": "Create an event, then add participants from the Participants menu.",
                "href": url_for("events"),
                "label": "Events",
            }
        )
    if role == "athlete" and not profile:
        hints.append(
            {
                "text": "Complete your athlete profile and join one event.",
                "href": url_for("athlete_profile"),
                "label": "My Profile",
            }
        )
    return render_template("dashboard.html", profile=profile, counts=counts, hints=hints)


@app.route("/departments", methods=["GET", "POST"])
@require_login(["admin"])
def departments():
    form = {"deptID": "", "deptName": ""}
    if request.method == "POST":
        action = request.form.get("action")
        if action == "rename":
            ok, message = db.rename_department(
                request.form.get("deptID"),
                request.form.get("deptName"),
            )
        else:
            form["deptID"] = request.form.get("deptID") or ""
            form["deptName"] = request.form.get("deptName") or ""
            ok, message = db.add_department(form["deptID"], form["deptName"])
        flash(message, "success" if ok else "error")
        if ok:
            return redirect(url_for("departments"))
    return render_template("departments.html", departments=db.get_departments(), form=form)


@app.route("/registrations")
@require_login(["admin"])
def users():
    return render_template("users.html", users=db.get_users())


@app.route("/tournament-managers")
@require_login(["admin"])
def managers():
    return render_people("tournament manager")


@app.route("/coaches")
@require_login(["admin"])
def coaches():
    return render_people("coach")


@app.route("/deans")
@require_login(["admin"])
def deans():
    return render_people("dean")


@app.route("/profile", methods=["GET", "POST"])
@require_login(["coach", "dean", "tournament manager"])
def profile():
    role = session["role"]
    username = session["userName"]
    record = db.get_staff(role, username)
    posted = None
    if request.method == "POST":
        posted = {
            "fName": request.form.get("fName") or "",
            "lName": request.form.get("lName") or "",
            "mobile": request.form.get("mobile") or "",
            "deptID": record["deptID"] if record else (request.form.get("deptID") or "").strip().upper(),
            "deptName": record["deptName"] if record else "",
        }
        ok, message = db.save_staff(
            role,
            username,
            posted["fName"],
            posted["lName"],
            posted["mobile"],
            posted["deptID"],
        )
        flash(message, "success" if ok else "error")
        if ok:
            return redirect(url_for("profile"))
    return render_template(
        "profile.html",
        profile=db.get_staff(role, username),
        posted=posted,
        departments=db.get_departments(),
        page_title=PROFILE_TITLES[role],
        table_name=STAFF_TABLE[role],
        lock_department=record is not None,
    )


@app.route("/events", methods=["GET", "POST"])
@require_login()
def events():
    role = session["role"]
    username = session["userName"]
    manager_profile = db.get_staff("tournament manager", username) if role == "tournament manager" else None
    managers = db.list_staff("tournament manager") if role == "admin" else []
    event_form = {
        "category": "",
        "eventName": "",
        "noOfParticipant": "",
        "eventID": "",
        "tournamentManager": username if role == "tournament manager" else "",
    }
    if request.method == "POST" and request.form.get("action") == "register":
        if role != "athlete":
            flash("Only a student can register for an event.", "error")
            return redirect(url_for("events"))
        event = db.get_event(request.form.get("eventID"))
        if not event:
            flash("That event does not exist.", "error")
            return redirect(url_for("events"))
        athlete = db.get_athlete(username)
        if not athlete:
            flash(f"Save your profile to register for {event['eventName']}.", "info")
            return redirect(url_for("athlete_profile", event=event["eventID"]))
        if athlete["eventID"] == event["eventID"]:
            flash(f"You are already registered for {event['eventName']}.", "info")
            return redirect(url_for("events"))
        ok, message = db.save_athlete(username, profile_payload(athlete, event["eventID"]))
        if ok:
            message = f"You are registered for {event['eventName']}."
        flash(message, "success" if ok else "error")
        return redirect(url_for("events"))
    if request.method == "POST":
        if role not in ("admin", "tournament manager"):
            flash("Only an admin or a tournament manager can save events.", "error")
            return redirect(url_for("events"))
        manager = username if role == "tournament manager" else (request.form.get("tournamentManager") or "")
        event_form = {
            "category": request.form.get("category") or "",
            "eventName": request.form.get("eventName") or "",
            "noOfParticipant": request.form.get("noOfParticipant") or "",
            "eventID": request.form.get("eventID") or "",
            "tournamentManager": manager.strip().upper(),
        }
        ok, message = db.save_event(
            event_form["tournamentManager"],
            event_form["category"],
            event_form["eventName"],
            event_form["noOfParticipant"],
            event_form["eventID"] or None,
            allow_any=(role == "admin"),
        )
        flash(message, "success" if ok else "error")
        if ok:
            return redirect(url_for("events"))
    elif request.args.get("edit") and role in ("admin", "tournament manager"):
        editing = db.get_event(request.args.get("edit"))
        if editing and (role == "admin" or editing["tournamentManager"] == username):
            event_form = {
                "category": editing["category"],
                "eventName": editing["eventName"],
                "noOfParticipant": editing["noOfParticipant"],
                "eventID": editing["eventID"],
                "tournamentManager": editing["tournamentManager"],
            }
    show_form = (role == "tournament manager" and manager_profile) or (role == "admin" and bool(managers))
    athlete = db.get_athlete(username) if role == "athlete" else None
    return render_template(
        "events.html",
        events=db.get_events(),
        profile=manager_profile,
        event_form=event_form,
        managers=managers,
        show_form=show_form,
        athlete_event_id=athlete["eventID"] if athlete else None,
    )


@app.route("/my-profile", methods=["GET", "POST"])
@require_login(["athlete"])
def athlete_profile():
    username = session["userName"]
    profile = db.get_athlete(username)
    departments = db.get_departments()
    coaches = db.list_staff("coach")
    deans = db.list_staff("dean")
    events = db.get_events()
    missing = []
    if not departments:
        missing.append("Department — an admin creates this under Departments.")
    if not events:
        missing.append("Event — an admin or tournament manager creates this under Events.")
    if not coaches:
        missing.append("Coach — a coach must save a profile.")
    if not deans:
        missing.append("Dean — a dean must save a profile.")
    form = athlete_form_values(profile)
    if request.method == "GET" and not profile and request.args.get("event"):
        form["eventID"] = request.args.get("event")
    if request.method == "POST":
        form = athlete_form_values(profile, request.form)
        if missing:
            flash("Athlete profiles open after a department, event, coach, and dean exist.", "error")
        else:
            ok, message = db.save_athlete(username, form)
            flash(message, "success" if ok else "error")
            if ok:
                return redirect(url_for("athlete_profile"))
    return render_template(
        "athlete_profile.html",
        form=form,
        editing=profile is not None,
        id_num=username,
        departments=departments,
        coaches=coaches,
        deans=deans,
        events=events,
        missing=missing,
    )


@app.route("/athletes", methods=["GET", "POST"])
@require_login(["admin", "coach", "dean", "tournament manager"])
def athletes():
    role = session["role"]
    username = session["userName"]
    can_add = role in ("admin", "tournament manager", "dean", "coach")
    dean_dept = ""
    dean_name = ""
    staff_dept = ""
    staff_dept_name = ""
    if role == "coach":
        profile = db.get_staff("coach", username)
        if not profile:
            flash("Save your coach profile first.", "info")
            return redirect(url_for("profile"))
        rows = db.get_athletes(dept_id=profile["deptID"])
        staff_dept = profile["deptID"]
        staff_dept_name = profile["deptName"]
        empty_message = "No students in your department yet. Register one below for an event."
        title = "Department Students"
        scope = f"{profile['deptName']} ({profile['deptID']})"
    elif role == "dean":
        profile = db.get_staff("dean", username)
        if not profile:
            flash("Save your dean profile first.", "info")
            return redirect(url_for("profile"))
        rows = db.get_athletes(dept_id=profile["deptID"])
        dean_dept = profile["deptID"]
        dean_name = profile["deptName"]
        staff_dept = profile["deptID"]
        staff_dept_name = profile["deptName"]
        empty_message = "No participants in your department yet."
        title = "Department Participants"
        scope = f"{profile['deptName']} ({profile['deptID']})"
    elif role == "tournament manager":
        profile = db.get_staff("tournament manager", username)
        if not profile:
            flash("Save your tournament manager profile first.", "info")
            return redirect(url_for("profile"))
        rows = db.get_athletes(dept_id=profile["deptID"])
        staff_dept = profile["deptID"]
        staff_dept_name = profile["deptName"]
        empty_message = "No participants in your department yet. They appear when the dean adds a student to this department."
        title = "Department Participants"
        scope = f"{profile['deptName']} ({profile['deptID']})"
    else:
        rows = db.get_athletes()
        empty_message = "No participants yet."
        title = "Participants"
        scope = ""

    form = {key: "" for key in ("idNum",) + ATHLETE_FIELDS}
    missing = []
    accounts = []
    departments = []
    coaches = []
    deans = []
    event_choices = []
    editing = False
    if can_add:
        all_events = db.get_events()
        if role == "dean":
            departments = [db.get_department(dean_dept)]
            coaches = [coach for coach in db.list_staff("coach") if coach["deptID"] == dean_dept]
            deans = [db.get_staff("dean", username)]
            accounts = db.list_athlete_accounts(dean_dept)
            event_choices = all_events
        elif role == "coach":
            departments = [db.get_department(staff_dept)]
            coaches = [db.get_staff("coach", username)]
            deans = [person for person in db.list_staff("dean") if person["deptID"] == staff_dept]
            accounts = db.list_athlete_accounts(staff_dept)
            event_choices = all_events
        else:
            departments = db.get_departments()
            coaches = db.list_staff("coach")
            deans = db.list_staff("dean")
            accounts = db.list_athlete_accounts()
            if role == "tournament manager":
                departments = [db.get_department(staff_dept)]
                coaches = [coach for coach in coaches if coach["deptID"] == staff_dept]
                deans = [person for person in deans if person["deptID"] == staff_dept]
                accounts = db.list_athlete_accounts(staff_dept)
                event_choices = [event for event in all_events if event["tournamentManager"] == username]
            else:
                event_choices = all_events
        if not departments or not departments[0]:
            missing.append("Department — the admin creates this under Departments.")
        if not coaches:
            if role == "dean":
                missing.append(f"Coach — a coach in {dean_dept} must open My Profile and save it.")
            else:
                missing.append("Coach — a coach must open My Profile and save it.")
        if not deans or not deans[0]:
            if role == "coach":
                missing.append(f"Dean — a dean in {staff_dept} must be registered before you can place a student in an event.")
            else:
                missing.append("Dean — a dean must open My Profile and save it.")
        if not event_choices:
            missing.append("Event — create one under Events, linked to a tournament manager.")
        if not accounts:
            if role in ("dean", "coach", "tournament manager"):
                missing.append(f"Student — none are available for {staff_dept}. Students register on the home page.")
            else:
                missing.append("Student account — the student registers on the home page, or the admin registers them.")

        if request.method == "POST":
            selected = (request.form.get("idNum") or "").strip().upper()
            form = athlete_form_values(None, request.form)
            form["idNum"] = selected
            if role not in ("admin", "tournament manager", "dean", "coach"):
                flash("Only an admin, tournament manager, dean, or coach can register a student for an event.", "error")
                return redirect(url_for("athletes"))
            if missing:
                flash("Add a participant after the department, coach, dean, event, and student account exist.", "error")
            elif not selected:
                flash("Choose the student to add.", "error")
            else:
                event = db.get_event(form["eventID"])
                existing = db.get_athlete(selected)
                blocked = None
                if role == "tournament manager":
                    form["deptID"] = staff_dept
                    if not event or event["tournamentManager"] != username:
                        blocked = "You can only add participants to your own events."
                    elif existing and existing["deptID"] != staff_dept:
                        blocked = "You can only see participants from your department."
                    else:
                        coach = db.get_staff("coach", form.get("coachID"))
                        person = db.get_staff("dean", form.get("deanID"))
                        if not coach or coach["deptID"] != staff_dept or not person or person["deptID"] != staff_dept:
                            blocked = "Choose a coach and dean from your department."
                elif role == "dean":
                    form["deptID"] = dean_dept
                    form["deanID"] = username
                    if existing and existing["deptID"] != dean_dept:
                        blocked = "You can only select participants from your department."
                    else:
                        coach = db.get_staff("coach", form.get("coachID"))
                        if not coach or coach["deptID"] != dean_dept:
                            blocked = "Choose a coach from your department."
                elif role == "coach":
                    form["deptID"] = staff_dept
                    form["coachID"] = username
                    if not event:
                        blocked = "Choose an event."
                    elif existing and existing["deptID"] != staff_dept:
                        blocked = "You can only register students from your department."
                    else:
                        person = db.get_staff("dean", form.get("deanID"))
                        if not person or person["deptID"] != staff_dept:
                            blocked = "Choose a dean from your department."
                if blocked:
                    flash(blocked, "error")
                else:
                    ok, message = db.save_athlete(selected, form)
                    if ok and role == "coach":
                        message = "Student registered for the event."
                    elif ok:
                        message = "Participant updated." if existing else "Participant added."
                    flash(message, "success" if ok else "error")
                    if ok:
                        return redirect(url_for("athletes"))
            editing = db.athlete_exists(selected)
        else:
            selected = (request.args.get("id") or "").strip().upper()
            existing = db.get_athlete(selected) if selected else None
            if existing and role == "tournament manager" and existing["deptID"] != staff_dept:
                flash("You can only see participants from your department.", "error")
                return redirect(url_for("athletes"))
            if existing and role == "dean" and existing["deptID"] != dean_dept:
                flash("You can only select participants from your department.", "error")
                return redirect(url_for("athletes"))
            if existing and role == "coach" and existing["deptID"] != staff_dept:
                flash("You can only register students from your department.", "error")
                return redirect(url_for("athletes"))
            form = athlete_form_values(existing)
            form["idNum"] = selected
            if role == "dean":
                form["deptID"] = dean_dept
                form["deanID"] = username
            elif role == "tournament manager":
                form["deptID"] = staff_dept
            elif role == "coach":
                form["deptID"] = staff_dept
                form["coachID"] = username
            if not existing and request.args.get("event"):
                form["eventID"] = request.args.get("event")
            editing = existing is not None

    return render_template(
        "athletes.html",
        athletes=rows,
        empty_message=empty_message,
        title=title,
        can_add=can_add,
        missing=missing,
        form=form,
        athlete_accounts=accounts,
        departments=departments,
        coaches=coaches,
        deans=deans,
        events=event_choices,
        editing=editing,
        locked_dept=staff_dept if role in ("dean", "tournament manager", "coach") else "",
        locked_dept_name=staff_dept_name if role in ("dean", "tournament manager", "coach") else "",
        locked_dean=username if role == "dean" else "",
        locked_coach=username if role == "coach" else "",
        scope=scope,
    )


@app.errorhandler(404)
def not_found(_error):
    return render_template("message.html", heading="Page not found", text="That page is not in the menu."), 404


if __name__ == "__main__":
    print("UC Main Intramurals System")
    print(f"Local Admin ID: {LOCAL_ADMIN_ID}")
    print(f"Password: {LOCAL_ADMIN_PASSWORD}")
    print("Open http://127.0.0.1:5000")
    app.run(debug=True)
