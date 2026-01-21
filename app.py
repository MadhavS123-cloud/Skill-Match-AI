from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "skill-match-secret"


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin123":
            session["user"] = "admin"
            return redirect(url_for("index"))
        else:
            error = "Invalid username or password"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


@app.route("/", methods=["GET", "POST"])
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("index.html")


if __name__ == "__main__":
    print(app.url_map)
    app.run(debug=True)
