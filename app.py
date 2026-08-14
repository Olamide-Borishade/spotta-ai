import json
import os

import requests
from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from db import create_user, get_progress_for_user, get_user_by_username, init_db, log_progress, verify_login
from logic.agents import ask_assistant
from logic.ranking import estimate_confidence, geocode_destination, haversine_distance, rank_spots

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")  # TODO: set SECRET_KEY env var in production
init_db()

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "spots.json")

# Fallback origin (downtown Vancouver) used when geocoding fails or returns no match.
DEFAULT_ORIGIN = (49.2827, -123.1207)


@app.context_processor
def inject_auth():
    return {
        "logged_in": "user_id" in session,
        "username": session.get("username"),
    }


def load_spots():
    with open(DATA_PATH) as f:
        return json.load(f)


def load_spots_with_distance(origin):
    spots = load_spots()
    origin_lat, origin_lng = origin
    for spot in spots:
        spot["distance_km"] = round(
            haversine_distance(origin_lat, origin_lng, spot["lat"], spot["lng"]), 2
        )

    prices = [spot["price_per_hour"] for spot in spots]
    price_range = (min(prices), max(prices))
    for spot in spots:
        spot["confidence"] = estimate_confidence(spot, price_range)

    return spots


def attach_confidence_labels(spots):
    for spot in spots:
        confidence = spot["confidence"]
        if confidence >= 0.80:
            spot["confidence_tier"] = "high"
            spot["confidence_label"] = "Likely open"
        elif confidence >= 0.60:
            spot["confidence_tier"] = "medium"
            spot["confidence_label"] = "Uncertain"
        else:
            spot["confidence_tier"] = "low"
            spot["confidence_label"] = "Often full"
    return spots


@app.route("/", methods=["GET", "POST"])
def index():
    destination = None
    results = None
    error = None

    if request.method == "POST":
        destination = request.form.get("destination", "").strip()

        if not destination:
            error = "Please enter a destination to search."
        else:
            geocoded = geocode_destination(destination)
            if geocoded is None:
                results = []
            else:
                results = attach_confidence_labels(rank_spots(load_spots_with_distance(geocoded)))

    return render_template("index.html", destination=destination, results=results, error=error)


@app.route("/navigate/<int:spot_id>")
def navigate(spot_id):
    spot = next((s for s in load_spots_with_distance(DEFAULT_ORIGIN) if s["id"] == spot_id), None)
    if spot is None:
        return "Spot not found", 404

    user_id = session.get("user_id")
    if user_id is not None:
        log_progress(user_id, spot_id, status="navigating")

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


@app.route("/assistant", methods=["POST"])
def assistant():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    model = data.get("model") or None

    if not message:
        return jsonify({"reply": "Please enter a question."}), 400

    try:
        reply = ask_assistant(message, model=model)
    except RuntimeError:
        return jsonify({"reply": "The Spotta Assistant isn't configured yet. Ask the site owner to add an OpenRouter API key."})
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        return jsonify({"reply": f"The assistant couldn't reach that model (error {status}). Try the free model, or check that model has OpenRouter credits."})
    except requests.exceptions.RequestException:
        return jsonify({"reply": "The assistant is temporarily unavailable. Please try again."})
    except (KeyError, IndexError):
        return jsonify({"reply": "The model sent back an unexpected response. Please try again."})

    return jsonify({"reply": reply})


@app.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for("login"))

    progress = get_progress_for_user(user_id)
    return render_template("dashboard.html", progress=progress)


if __name__ == "__main__":
    app.run(debug=True)
