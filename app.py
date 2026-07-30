import json
import os

from flask import Flask, redirect, render_template, request, session, url_for

from db import create_user, get_progress_for_user, get_user_by_username, init_db, verify_login
from logic.ranking import rank_spots

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")  # TODO: set SECRET_KEY env var in production
init_db()

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "spots.json")


@app.context_processor
def inject_auth():
    return {
        "logged_in": "user_id" in session,
        "username": session.get("username"),
    }


def load_spots():
    with open(DATA_PATH) as f:
        return json.load(f)


@app.route("/", methods=["GET", "POST"])
def index():
    destination = None
    results = None

    if request.method == "POST":
        destination = request.form.get("destination", "").strip()
        results = rank_spots(load_spots())

    return render_template("index.html", destination=destination, results=results)


@app.route("/navigate/<int:spot_id>")
def navigate(spot_id):
    spot = next((s for s in load_spots() if s["id"] == spot_id), None)
    if spot is None:
        return "Spot not found", 404

    return render_template("navigate.html", spot=spot)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            error = "Username and password are required."
        elif get_user_by_username(username) is not None:
            error = "That username is already taken."
        else:
            user_id = create_user(username, password)
            session["user_id"] = user_id
            session["username"] = username
            return redirect(url_for("dashboard"))

    return render_template("signup.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = verify_login(username, password)

        if user is None:
            error = "Invalid username or password."
        else:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for("login"))

    progress = get_progress_for_user(user_id)
    return render_template("dashboard.html", progress=progress)


if __name__ == "__main__":
    app.run(debug=True)
