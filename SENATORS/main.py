import os

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

import dbhelper

app = Flask(__name__)
app.secret_key = "philippine-national-election-local"


@app.context_processor
def inject_helpers():
    return {"person_name": dbhelper.person_name}


def require_text(*values):
    return all(value.strip() for value in values)


def read_seats(raw):
    try:
        seats = int(raw)
    except (TypeError, ValueError):
        return None
    if seats < 1:
        return None
    return seats


def read_status(raw):
    if raw in ("active", "inactive"):
        return raw
    return None


@app.route("/")
def home():
    if not os.path.exists(dbhelper.DB_NAME):
        abort(500, "Election.db is missing. Create it with sqlite3.exe and schema.sql.")
    return render_template("index.html", counts=dbhelper.get_counts())


@app.route("/positions")
def positions():
    return render_template("positions.html", positions=dbhelper.get_positions())


@app.route("/positions/add", methods=["GET", "POST"])
def add_position():
    if request.method == "POST":
        pos_name = request.form.get("posName", "").strip()
        seats = read_seats(request.form.get("numOfPositions", "").strip())
        pos_stat = read_status(request.form.get("posStat"))
        if not pos_name:
            flash("Position name is required.", "error")
        elif seats is None:
            flash("Number of seats must be a whole number of at least 1.", "error")
        elif pos_stat is None:
            flash("Select a valid status.", "error")
        else:
            dbhelper.add_position(pos_name, seats, pos_stat)
            flash("Position added.", "success")
            return redirect(url_for("positions"))
    return render_template("position_form.html", position=None)


@app.route("/positions/edit/<int:pos_id>", methods=["GET", "POST"])
def edit_position(pos_id):
    position = dbhelper.get_position(pos_id)
    if position is None:
        abort(404)
    if request.method == "POST":
        pos_name = request.form.get("posName", "").strip()
        seats = read_seats(request.form.get("numOfPositions", "").strip())
        pos_stat = read_status(request.form.get("posStat"))
        if not pos_name:
            flash("Position name is required.", "error")
        elif seats is None:
            flash("Number of seats must be a whole number of at least 1.", "error")
        elif pos_stat is None:
            flash("Select a valid status.", "error")
        else:
            dbhelper.update_position(pos_id, pos_name, seats, pos_stat)
            flash("Position updated.", "success")
            return redirect(url_for("positions"))
    return render_template("position_form.html", position=position)


@app.route("/positions/deactivate/<int:pos_id>", methods=["POST"])
def deactivate_position(pos_id):
    if dbhelper.get_position(pos_id) is None:
        abort(404)
    dbhelper.deactivate_position(pos_id)
    flash("Position deactivated.", "success")
    return redirect(url_for("positions"))


@app.route("/candidates")
def candidates():
    return render_template("candidates.html", candidates=dbhelper.get_candidates())


@app.route("/candidates/add", methods=["GET", "POST"])
def add_candidate():
    positions = dbhelper.get_positions()
    if request.method == "POST":
        first = request.form.get("candFName", "").strip()
        middle = request.form.get("candMName", "").strip()
        last = request.form.get("candLName", "").strip()
        cand_stat = read_status(request.form.get("candStat"))
        try:
            pos_id = int(request.form.get("posID", ""))
        except ValueError:
            pos_id = None
        if not require_text(first, last):
            flash("First name and last name are required.", "error")
        elif pos_id is None or cand_stat is None:
            flash("Select a position and a valid status.", "error")
        else:
            try:
                dbhelper.add_candidate(first, middle, last, pos_id, cand_stat)
            except ValueError as exc:
                flash(str(exc), "error")
            else:
                flash("Candidate added.", "success")
                return redirect(url_for("candidates"))
    return render_template("candidate_form.html", candidate=None, positions=positions)


@app.route("/candidates/edit/<int:cand_id>", methods=["GET", "POST"])
def edit_candidate(cand_id):
    candidate = dbhelper.get_candidate(cand_id)
    if candidate is None:
        abort(404)
    positions = dbhelper.get_positions()
    if request.method == "POST":
        first = request.form.get("candFName", "").strip()
        middle = request.form.get("candMName", "").strip()
        last = request.form.get("candLName", "").strip()
        cand_stat = read_status(request.form.get("candStat"))
        try:
            pos_id = int(request.form.get("posID", ""))
        except ValueError:
            pos_id = None
        if not require_text(first, last):
            flash("First name and last name are required.", "error")
        elif pos_id is None or cand_stat is None:
            flash("Select a position and a valid status.", "error")
        else:
            try:
                dbhelper.update_candidate(cand_id, first, middle, last, pos_id, cand_stat)
            except ValueError as exc:
                flash(str(exc), "error")
            else:
                flash("Candidate updated.", "success")
                return redirect(url_for("candidates"))
    return render_template(
        "candidate_form.html",
        candidate=candidate,
        positions=positions,
    )


@app.route("/candidates/deactivate/<int:cand_id>", methods=["POST"])
def deactivate_candidate(cand_id):
    if dbhelper.get_candidate(cand_id) is None:
        abort(404)
    dbhelper.deactivate_candidate(cand_id)
    flash("Candidate deactivated.", "success")
    return redirect(url_for("candidates"))


@app.route("/voters")
def voters():
    return render_template("voters.html", voters=dbhelper.get_voters())


@app.route("/voters/add", methods=["GET", "POST"])
def add_voter():
    if request.method == "POST":
        voter_id = request.form.get("voterID", "").strip()
        voter_pass = request.form.get("voterPass", "")
        first = request.form.get("voterFName", "").strip()
        middle = request.form.get("voterMName", "").strip()
        last = request.form.get("voterLName", "").strip()
        voter_stat = read_status(request.form.get("voterStat"))
        if not voter_id or not voter_pass or not require_text(first, last):
            flash("Voter ID, password, first name, and last name are required.", "error")
        elif voter_stat is None:
            flash("Select a valid status.", "error")
        else:
            try:
                dbhelper.add_voter(voter_id, voter_pass, first, middle, last, voter_stat)
            except ValueError as exc:
                flash(str(exc), "error")
            else:
                flash("Voter added.", "success")
                return redirect(url_for("voters"))
    return render_template("voter_form.html", voter=None)


@app.route("/voters/edit/<voter_id>", methods=["GET", "POST"])
def edit_voter(voter_id):
    voter = dbhelper.get_voter(voter_id)
    if voter is None:
        abort(404)
    if request.method == "POST":
        voter_pass = request.form.get("voterPass", "")
        first = request.form.get("voterFName", "").strip()
        middle = request.form.get("voterMName", "").strip()
        last = request.form.get("voterLName", "").strip()
        voter_stat = read_status(request.form.get("voterStat"))
        if not voter_pass or not require_text(first, last):
            flash("Password, first name, and last name are required.", "error")
        elif voter_stat is None:
            flash("Select a valid status.", "error")
        else:
            dbhelper.update_voter(voter_id, voter_pass, first, middle, last, voter_stat)
            flash("Voter updated.", "success")
            return redirect(url_for("voters"))
    return render_template("voter_form.html", voter=voter)


@app.route("/voters/deactivate/<voter_id>", methods=["POST"])
def deactivate_voter(voter_id):
    if dbhelper.get_voter(voter_id) is None:
        abort(404)
    dbhelper.deactivate_voter(voter_id)
    flash("Voter deactivated.", "success")
    return redirect(url_for("voters"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        voter_id = request.form.get("voterID", "").strip()
        voter_pass = request.form.get("voterPass", "")
        voter = dbhelper.authenticate(voter_id, voter_pass)
        if voter is None:
            flash("Invalid voter ID or password.", "error")
        elif voter["voterStat"] != "active":
            flash("Your account is inactive. You cannot vote.", "error")
        else:
            session["voterID"] = voter["voterID"]
            session["voterName"] = dbhelper.person_name(
                voter["voterFName"], voter["voterMName"], voter["voterLName"]
            )
            return redirect(url_for("vote"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.", "success")
    return redirect(url_for("login"))


@app.route("/vote", methods=["GET", "POST"])
def vote():
    voter_id = session.get("voterID")
    if not voter_id:
        return redirect(url_for("login"))
    voter = dbhelper.get_voter(voter_id)
    if voter is None:
        session.clear()
        return redirect(url_for("login"))

    blocked = None
    if voter["voterStat"] != "active":
        blocked = "inactive"
    elif voter["voted"] == "y":
        blocked = "voted"

    ballot = [] if blocked else dbhelper.get_ballot()
    if request.method == "POST":
        if blocked == "inactive":
            flash("Your account is inactive. You cannot vote.", "error")
            return redirect(url_for("vote"))
        if blocked == "voted":
            flash("You have already voted.", "error")
            return redirect(url_for("vote"))
        selections = []
        for item in ballot:
            position = item["position"]
            for cand_id in request.form.getlist(f"choice_{position['posID']}"):
                try:
                    selections.append((position["posID"], int(cand_id)))
                except ValueError:
                    flash("The ballot contained an invalid choice.", "error")
                    return render_template(
                        "vote.html",
                        voter=voter,
                        ballot=ballot,
                        blocked=None,
                        selected=request.form,
                    )
        try:
            dbhelper.cast_votes(voter["voterID"], selections)
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template(
                "vote.html",
                voter=voter,
                ballot=ballot,
                blocked=None,
                selected=request.form,
            )
        flash("Your ballot has been recorded. You cannot vote again.", "success")
        return redirect(url_for("vote"))

    return render_template(
        "vote.html",
        voter=voter,
        ballot=ballot,
        blocked=blocked,
        selected=None,
    )


@app.route("/results")
def results():
    return render_template("results.html", results=dbhelper.get_results())


@app.route("/winners")
def winners():
    return render_template("winners.html", winners=dbhelper.get_winners())


if __name__ == "__main__":
    if not os.path.exists(dbhelper.DB_NAME):
        raise SystemExit("Election.db is missing. Create it with sqlite3.exe and schema.sql.")
    app.run(debug=True)
