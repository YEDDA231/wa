from flask import Flask, render_template, request, redirect, url_for
import dbhelper

app = Flask(__name__)

# Create table if not exists
dbhelper.create_table()


# HOME (ADD + VIEW + SEARCH)
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        student_id = request.form["student_id"]
        name = request.form["name"]
        course = request.form["course"]
        score = request.form["score"]
        
        try:
            dbhelper.add_student(student_id, name, course, score)
        except:
            pass  # ignore duplicate ID

        return redirect(url_for("index"))

    keyword = request.args.get("search")

    if keyword:
        students = dbhelper.search_student(keyword)
    else:
        students = dbhelper.get_all_students()

    return render_template("index.html", students=students)


# EDIT
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    student = dbhelper.get_student(id)

    if request.method == "POST":
        name = request.form["name"]
        course = request.form["course"]
        score = request.form["score"]
        date_added = request.form["date_added"]
        dbhelper.update_student(id, name, course, score)
        return redirect(url_for("index"))

    return render_template("edit.html", student=student)

# DELETE
@app.route("/delete/<int:id>")
def delete(id):
    dbhelper.delete_student(id)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)