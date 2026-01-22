from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "skill-match-secret"

# TEMP in-memory user store (for demo)
users = {
    "admin": "admin123"
}


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username] == password:
            session["user"] = username
            return redirect(url_for("index"))
        else:
            error = "Invalid username or password"

    return render_template("login.html", error=error)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users:
            error = "User already exists"
        else:
            users[username] = password
            session["user"] = username
            return redirect(url_for("index"))

    return render_template("register.html", error=error)


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
