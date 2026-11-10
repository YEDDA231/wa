from datetime import date, datetime

from flask import Flask, flash, redirect, render_template, request, url_for

from database import init_db
import dbhelper as db


app = Flask(__name__)
app.secret_key = "dev-secret-key"  # replace with secure key for production

# Initialize the database once when the app module is imported.
# Flask 3 removed before_first_request, so we call init_db() here.
init_db()


def parse_date(date_str: str, fmt: str = "%Y-%m-%d"):
    try:
        datetime.strptime(date_str, fmt)
        return True, ""
    except ValueError:
        return False, f"Invalid date format. Please use {fmt.replace('%Y', 'YYYY').replace('%m', 'MM').replace('%d', 'DD')}"


def parse_datetime(dt_str: str, fmt: str = "%Y-%m-%d %H:%M"):
    try:
        datetime.strptime(dt_str, fmt)
        return True, ""
    except ValueError:
        return False, "Invalid date/time. Please use YYYY-MM-DD HH:MM (24-hour clock)."


def to_24h_datetime(date_str: str, time_str: str, meridiem: str) -> str:
    """
    Convert date + 12-hour time + meridiem to 'YYYY-MM-DD HH:MM' (24-hour) string.
    Expects:
      date_str: 'YYYY-MM-DD'
      time_str: 'HH:MM' where HH is 01-12
      meridiem: 'AM' or 'PM' (case-insensitive)
    """
    mer = (meridiem or "").strip().upper()
    if mer not in ("AM", "PM"):
        raise ValueError("Please select AM or PM.")

    try:
        hour_str, minute_str = (time_str or "").strip().split(":")
        hour = int(hour_str)
        minute = int(minute_str)
    except Exception as exc:
        raise ValueError("Invalid time. Please use HH:MM.") from exc

    if hour < 1 or hour > 12 or minute < 0 or minute > 59:
        raise ValueError("Invalid time. Hour must be 1-12 and minute 00-59.")

    if mer == "AM":
        hour24 = 0 if hour == 12 else hour
    else:
        hour24 = 12 if hour == 12 else hour + 12

    # validate date and return normalized string
    try:
        d = datetime.strptime((date_str or "").strip(), "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("Invalid date. Please use YYYY-MM-DD.") from exc

    return f"{d.isoformat()} {hour24:02d}:{minute:02d}"


@app.route("/")
def index():
    return render_template("index.html")


# ---------- Veterinarian Management ----------

@app.route("/vets")
def vets_list():
    q = request.args.get("q", "").strip()
    vets = db.search_vets(q)
    return render_template("vets.html", vets=vets, q=q)


@app.route("/vets/new", methods=["GET", "POST"])
def vets_new():
    if request.method == "POST":
        data = {
            "vetID": request.form.get("vetID", "").strip(),
            "vetFName": request.form.get("vetFName", "").strip(),
            "vetLName": request.form.get("vetLName", "").strip(),
            "vetAddress": request.form.get("vetAddress", "").strip(),
            "vetSpecial": request.form.get("vetSpecial", "").strip(),
        }
        if not all(data.values()):
            flash("All fields are required.", "danger")
            return render_template("vet_form.html", vet=data, mode="new")
        try:
            db.create_vet(data)
            flash("Veterinarian created successfully.", "success")
            return redirect(url_for("vets_list"))
        except Exception as exc:
            flash(f"Error saving veterinarian: {exc}", "danger")
            return render_template("vet_form.html", vet=data, mode="new")
    return render_template("vet_form.html", vet={}, mode="new")


@app.route("/vets/<vet_id>/edit", methods=["GET", "POST"])
def vets_edit(vet_id):
    vet = db.get_vet(vet_id)
    if not vet:
        flash("Veterinarian not found.", "warning")
        return redirect(url_for("vets_list"))
    if request.method == "POST":
        data = {
            "vetFName": request.form.get("vetFName", "").strip(),
            "vetLName": request.form.get("vetLName", "").strip(),
            "vetAddress": request.form.get("vetAddress", "").strip(),
            "vetSpecial": request.form.get("vetSpecial", "").strip(),
        }
        if not all(data.values()):
            flash("All fields are required.", "danger")
            return render_template("vet_form.html", vet={**vet, **data}, mode="edit")
        try:
            db.update_vet(vet_id, data)
            flash("Veterinarian updated successfully.", "success")
            return redirect(url_for("vets_list"))
        except Exception as exc:
            flash(f"Error updating veterinarian: {exc}", "danger")
    return render_template("vet_form.html", vet=vet, mode="edit")


@app.route("/vets/<vet_id>/delete", methods=["POST"])
def vets_delete(vet_id):
    try:
        db.logical_delete_vet(vet_id)
        flash("Veterinarian deleted (logical).", "success")
    except Exception as exc:
        flash(f"Error deleting veterinarian: {exc}", "danger")
    return redirect(url_for("vets_list"))


# ---------- Pet Owner Management ----------

@app.route("/owners")
def owners_list():
    q = request.args.get("q", "").strip()
    owners = db.search_owners(q)
    return render_template("owners.html", owners=owners, q=q)


@app.route("/owners/new", methods=["GET", "POST"])
def owners_new():
    if request.method == "POST":
        data = {
            "petOwnerID": request.form.get("petOwnerID", "").strip(),
            "petOwnerFName": request.form.get("petOwnerFName", "").strip(),
            "petOwnerLName": request.form.get("petOwnerLName", "").strip(),
            "petOwnerBDate": request.form.get("petOwnerBDate", "").strip(),
            "petOwnerTelNo": request.form.get("petOwnerTelNo", "").strip(),
        }
        ok, msg = parse_date(data["petOwnerBDate"])
        if not ok:
            flash(msg, "danger")
            return render_template("owner_form.html", owner=data, mode="new")
        # Owner birth date cannot be in the future
        if datetime.strptime(data["petOwnerBDate"], "%Y-%m-%d").date() > date.today():
            flash("Owner birth date cannot be in the future.", "danger")
            return render_template("owner_form.html", owner=data, mode="new")
        if not all(data.values()):
            flash("All fields are required.", "danger")
            return render_template("owner_form.html", owner=data, mode="new")
        try:
            db.create_owner(data)
            flash("Pet owner created successfully.", "success")
            return redirect(url_for("owners_list"))
        except Exception as exc:
            flash(f"Error saving pet owner: {exc}", "danger")
            return render_template("owner_form.html", owner=data, mode="new")
    # pass today's date for max attribute in date input
    return render_template("owner_form.html", owner={}, mode="new", caller_today=date.today().isoformat())


@app.route("/owners/<owner_id>/edit", methods=["GET", "POST"])
def owners_edit(owner_id):
    owner = db.get_owner(owner_id)
    if not owner:
        flash("Pet owner not found.", "warning")
        return redirect(url_for("owners_list"))
    if request.method == "POST":
        data = {
            "petOwnerFName": request.form.get("petOwnerFName", "").strip(),
            "petOwnerLName": request.form.get("petOwnerLName", "").strip(),
            "petOwnerBDate": request.form.get("petOwnerBDate", "").strip(),
            "petOwnerTelNo": request.form.get("petOwnerTelNo", "").strip(),
        }
        ok, msg = parse_date(data["petOwnerBDate"])
        if not ok:
            flash(msg, "danger")
            return render_template("owner_form.html", owner={**owner, **data}, mode="edit")
        if not all(data.values()):
            flash("All fields are required.", "danger")
            return render_template("owner_form.html", owner={**owner, **data}, mode="edit")
        try:
            db.update_owner(owner_id, data)
            flash("Pet owner updated successfully.", "success")
            return redirect(url_for("owners_list"))
        except Exception as exc:
            flash(f"Error updating pet owner: {exc}", "danger")
    return render_template("owner_form.html", owner=owner, mode="edit")


@app.route("/owners/<owner_id>/delete", methods=["POST"])
def owners_delete(owner_id):
    try:
        db.logical_delete_owner(owner_id)
        flash("Pet owner deleted (logical).", "success")
    except Exception as exc:
        flash(f"Error deleting pet owner: {exc}", "danger")
    return redirect(url_for("owners_list"))


# ---------- Pet Management ----------

@app.route("/pets")
def pets_list():
    q = request.args.get("q", "").strip()
    pets = db.search_pets(q)
    return render_template("pets.html", pets=pets, q=q)


@app.route("/pets/new", methods=["GET", "POST"])
def pets_new():
    owners = db.search_owners("")
    if request.method == "POST":
        data = {
            "petID": request.form.get("petID", "").strip(),
            "petName": request.form.get("petName", "").strip(),
            "petType": request.form.get("petType", "").strip(),
            "petSex": request.form.get("petSex", "").strip(),
            "petBDate": request.form.get("petBDate", "").strip(),
            "petOwnerID": request.form.get("petOwnerID", "").strip(),
        }
        ok, msg = parse_date(data["petBDate"])
        if not ok:
            flash(msg, "danger")
            return render_template("pet_form.html", pet=data, owners=owners, mode="new")
        # Pet birth date cannot be in the future
        if datetime.strptime(data["petBDate"], "%Y-%m-%d").date() > date.today():
            flash("Pet birth date cannot be in the future.", "danger")
            return render_template("pet_form.html", pet=data, owners=owners, mode="new")
        if not all(data.values()):
            flash("All fields are required.", "danger")
            return render_template("pet_form.html", pet=data, owners=owners, mode="new")
        try:
            db.create_pet(data)
            flash("Pet record created successfully.", "success")
            return redirect(url_for("pets_list"))
        except Exception as exc:
            # Handle duplicate petID (UNIQUE constraint) gracefully
            if "UNIQUE constraint failed: Pet.petID" in str(exc):
                flash("Pet ID already exists. Please use a different Pet ID.", "danger")
            else:
                flash(f"Error saving pet: {exc}", "danger")
            return render_template("pet_form.html", pet=data, owners=owners, mode="new")
    return render_template("pet_form.html", pet={}, owners=owners, mode="new", caller_today=date.today().isoformat())


@app.route("/pets/<pet_id>/edit", methods=["GET", "POST"])
def pets_edit(pet_id):
    pet = db.get_pet(pet_id)
    if not pet:
        flash("Pet not found.", "warning")
        return redirect(url_for("pets_list"))
    owners = db.search_owners("")
    if request.method == "POST":
        data = {
            "petName": request.form.get("petName", "").strip(),
            "petType": request.form.get("petType", "").strip(),
            "petSex": request.form.get("petSex", "").strip(),
            "petBDate": request.form.get("petBDate", "").strip(),
            "petOwnerID": request.form.get("petOwnerID", "").strip(),
        }
        ok, msg = parse_date(data["petBDate"])
        if not ok:
            flash(msg, "danger")
            return render_template(
                "pet_form.html", pet={**pet, **data}, owners=owners, mode="edit"
            )
        if not all(data.values()):
            flash("All fields are required.", "danger")
            return render_template(
                "pet_form.html", pet={**pet, **data}, owners=owners, mode="edit"
            )
        try:
            db.update_pet(pet_id, data)
            flash("Pet record updated successfully.", "success")
            return redirect(url_for("pets_list"))
        except Exception as exc:
            flash(f"Error updating pet: {exc}", "danger")
    return render_template("pet_form.html", pet=pet, owners=owners, mode="edit")


@app.route("/pets/<pet_id>/delete", methods=["POST"])
def pets_delete(pet_id):
    try:
        db.logical_delete_pet(pet_id)
        flash("Pet record deleted (logical).", "success")
    except Exception as exc:
        flash(f"Error deleting pet: {exc}", "danger")
    return redirect(url_for("pets_list"))


# ---------- Consultation Management ----------

@app.route("/consultations")
def consultations_list():
    q = request.args.get("q", "").strip()
    consultations = db.search_consultations(q)
    return render_template("consultations.html", consultations=consultations, q=q)


@app.route("/consultations/new", methods=["GET", "POST"])
def consultations_new():
    pets = db.search_pets("")
    vets = db.search_vets("")
    if request.method == "POST":
        consult_date_ymd = request.form.get("consultDateDate", "").strip()
        consult_time_hm = request.form.get("consultTime", "").strip()
        consult_ampm = request.form.get("consultMeridiem", "").strip()
        data = {
            "consultID": request.form.get("consultID", "").strip(),
            "petID": request.form.get("petID", "").strip(),
            "vetID": request.form.get("vetID", "").strip(),
            "consultDate": "",
            "diagnoses": request.form.get("diagnoses", "").strip(),
            "prescription": request.form.get("prescription", "").strip(),
        }
        # Convert to 24h string for storage
        try:
            data["consultDate"] = to_24h_datetime(consult_date_ymd, consult_time_hm, consult_ampm)
        except Exception as exc:
            flash(str(exc), "danger")
            return render_template(
                "consultation_form.html",
                consultation=data,
                pets=pets,
                vets=vets,
                mode="new",
            )
        ok, msg = parse_datetime(data["consultDate"])
        if not ok:
            flash(msg, "danger")
            return render_template(
                "consultation_form.html",
                consultation=data,
                pets=pets,
                vets=vets,
                mode="new",
            )
        if not all(data.values()):
            flash("All fields are required.", "danger")
            return render_template(
                "consultation_form.html",
                consultation=data,
                pets=pets,
                vets=vets,
                mode="new",
            )
        try:
            db.create_consultation(data)
            flash("Consultation created successfully.", "success")
            return redirect(url_for("consultations_list"))
        except Exception as exc:
            flash(f"Error saving consultation: {exc}", "danger")
            return render_template(
                "consultation_form.html",
                consultation=data,
                pets=pets,
                vets=vets,
                mode="new",
            )
    return render_template(
        "consultation_form.html",
        consultation={},
        pets=pets,
        vets=vets,
        mode="new",
    )


@app.route("/consultations/<consult_id>/edit", methods=["GET", "POST"])
def consultations_edit(consult_id):
    consultation = db.get_consultation(consult_id)
    if not consultation:
        flash("Consultation not found.", "warning")
        return redirect(url_for("consultations_list"))
    pets = db.search_pets("")
    vets = db.search_vets("")
    if request.method == "POST":
        consult_date_ymd = request.form.get("consultDateDate", "").strip()
        consult_time_hm = request.form.get("consultTime", "").strip()
        consult_ampm = request.form.get("consultMeridiem", "").strip()
        data = {
            "petID": request.form.get("petID", "").strip(),
            "vetID": request.form.get("vetID", "").strip(),
            "consultDate": "",
            "diagnoses": request.form.get("diagnoses", "").strip(),
            "prescription": request.form.get("prescription", "").strip(),
        }
        try:
            data["consultDate"] = to_24h_datetime(consult_date_ymd, consult_time_hm, consult_ampm)
        except Exception as exc:
            flash(str(exc), "danger")
            return render_template(
                "consultation_form.html",
                consultation={**consultation, **data},
                pets=pets,
                vets=vets,
                mode="edit",
            )
        ok, msg = parse_datetime(data["consultDate"])
        if not ok:
            flash(msg, "danger")
            return render_template(
                "consultation_form.html",
                consultation={**consultation, **data},
                pets=pets,
                vets=vets,
                mode="edit",
            )
        if not all(data.values()):
            flash("All fields are required.", "danger")
            return render_template(
                "consultation_form.html",
                consultation={**consultation, **data},
                pets=pets,
                vets=vets,
                mode="edit",
            )
        try:
            db.update_consultation(consult_id, data)
            flash("Consultation updated successfully.", "success")
            return redirect(url_for("consultations_list"))
        except Exception as exc:
            flash(f"Error updating consultation: {exc}", "danger")
    return render_template(
        "consultation_form.html",
        consultation=consultation,
        pets=pets,
        vets=vets,
        mode="edit",
    )


@app.route("/consultations/<consult_id>/delete", methods=["POST"])
def consultations_delete(consult_id):
    try:
        db.logical_delete_consultation(consult_id)
        flash("Consultation deleted (logical).", "success")
    except Exception as exc:
        flash(f"Error deleting consultation: {exc}", "danger")
    return redirect(url_for("consultations_list"))


# ---------- Inquiry / Reports ----------

@app.route("/inquiry", methods=["GET", "POST"])
def inquiry():
    result = None
    mode = request.form.get("mode") if request.method == "POST" else None
    value1 = request.form.get("value1", "") if request.method == "POST" else ""
    value2 = request.form.get("value2", "") if request.method == "POST" else ""

    if request.method == "POST":
        try:
            if mode == "special":
                result = db.vets_by_specialization(value1.strip())
            elif mode == "pet":
                result = db.consultations_by_pet(value1.strip())
            elif mode == "owner":
                result = db.consultations_by_owner(value1.strip())
            elif mode == "vet":
                result = db.consultations_by_vet(value1.strip())
            elif mode == "date":
                from_ok, msg1 = parse_date(value1.strip())
                to_ok, msg2 = parse_date(value2.strip())
                if not from_ok:
                    raise ValueError(msg1)
                if not to_ok:
                    raise ValueError(msg2)
                result = db.consultations_between_dates(value1.strip(), value2.strip())
            else:
                flash("Please select a valid inquiry type.", "warning")
        except Exception as exc:
            flash(f"Error running inquiry: {exc}", "danger")

    return render_template(
        "inquiry.html", mode=mode, value1=value1, value2=value2, result=result
    )


if __name__ == "__main__":
    # Use single-threaded dev server to avoid concurrent SQLite writes
    app.run(debug=True, threaded=False)

