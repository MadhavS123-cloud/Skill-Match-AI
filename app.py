from flask import Flask, render_template, redirect, url_for, session
from flask_dance.contrib.google import make_google_blueprint, google
import os

app = Flask(__name__)
app.secret_key = "dev-secret-key"

google_bp = make_google_blueprint(
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    scope=["profile", "email"]
)

app.register_blueprint(google_bp, url_prefix="/login")

from flask_dance.contrib.google import google

@app.route("/")
def index():
    if not google.authorized:
        return redirect(url_for("login"))

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return "Failed to fetch user info"

    user_info = resp.json()
    return render_template(
        "index.html",
        user=user_info
    )
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/login")
def login():
    if google.authorized:
        return redirect(url_for("index"))
    return render_template("login.html")
@app.route("/register")
def register():
    if google.authorized:
        return redirect(url_for("index"))
    return render_template("register.html")

if __name__ == "__main__":
    print(app.url_map)
    app.run(debug=True)
