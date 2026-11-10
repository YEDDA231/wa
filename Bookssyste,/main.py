from flask import Flask, render_template, request
import dbhelper

app = Flask(__name__)

# ✅ Create table first, then seed
dbhelper.create_table()
dbhelper.seed_data()


@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    book = None

    if request.method == "POST":
        action = request.form.get("action")

        isbn = request.form.get("isbn")
        if isbn:
            isbn = int(isbn)

        if action == "search":
            book = dbhelper.get_book(isbn)
            if not book:
                message = "ITEM NOT FOUND"
            else:
                message = "ITEM FOUND"

        elif action == "add":
            message = dbhelper.add_book(
                isbn,
                request.form["title"],
                request.form["copyright"],
                request.form["edition"],
                request.form["price"],
                request.form["quantity"]
            )

        elif action == "update":
            message = dbhelper.update_book(
                isbn,
                request.form["title"],
                request.form["copyright"],
                request.form["edition"],
                request.form["price"],
                request.form["quantity"]
            )

        elif action == "delete":
            message = dbhelper.delete_book(isbn)

    books, total = dbhelper.get_all()

    return render_template(
        "index.html",
        books=books,
        total=total,
        message=message,
        book=book
    )


if __name__ == "__main__":
    app.run(debug=True)