import json
import os
import re
from datetime import datetime, timezone
from functools import wraps

import requests
from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from db import (
    VALID_SORTS,
    create_user,
    get_progress_for_user,
    get_user_by_username,
    init_db,
    log_progress,
    set_last_destination,
    set_preferred_sort,
    verify_login,
)
from logic import rag
from logic.agents import KB_PATH, PROMPT_PATH, ask_assistant
from logic.ranking import estimate_confidence, geocode_destination, haversine_distance, rank_spots

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")  # TODO: set SECRET_KEY env var in production
init_db()

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "spots.json")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "data", "results.json")

# Fallback origin (downtown Vancouver) used when geocoding fails or returns no match.
DEFAULT_ORIGIN = (49.2827, -123.1207)


@app.context_processor
def inject_auth():
    return {
        "logged_in": "user_id" in session,
        "username": session.get("username"),
        "role": session.get("role"),
    }


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            return "Forbidden", 403
        return view(*args, **kwargs)
    return wrapped


# Roles allowed to see retrieval citations (the "[Source N]" tags and the
# chunk text/similarity behind them). Everyone else gets a clean answer.
SOURCE_VISIBLE_ROLES = ("admin", "betatester")


def can_see_sources():
    return session.get("role") in SOURCE_VISIBLE_ROLES


CITATION_PATTERN = re.compile(r"\s*\[Source\s+\d+\]", re.IGNORECASE)


def strip_citations(text):
    cleaned = CITATION_PATTERN.sub("", text)
    return re.sub(r"[ \t]{2,}", " ", cleaned).strip()


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


SORT_KEYS = {
    "cheapest": lambda spot: spot["price_per_hour"],
    "closest": lambda spot: spot["distance_km"],
    "confidence": lambda spot: -spot["confidence"],
}


def apply_sort(spots, sort_by):
    key_fn = SORT_KEYS.get(sort_by)
    return sorted(spots, key=key_fn) if key_fn else spots


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


def load_results():
    if not os.path.exists(RESULTS_PATH):
        return []
    with open(RESULTS_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_result(entry):
    results = load_results()
    results.append(entry)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


@app.route("/", methods=["GET", "POST"])
def index():
    destination = None
    results = None
    error = None
    origin = None
    preferred_sort = session.get("preferred_sort", "best")
    # Lets other pages (e.g. the Workflows catalog) run a real search via a
    # plain link instead of duplicating the search form and its POST handler.
    run_agent = request.args.get("run_agent") == "1"

    if request.method == "POST":
        destination = request.form.get("destination", "").strip()
        search_requested = True
    elif request.args.get("destination") is not None:
        destination = request.args.get("destination", "").strip()
        search_requested = True
    else:
        search_requested = False

    if search_requested:
        if not destination:
            error = "Please enter a destination to search."
        else:
            if "user_id" in session:
                set_last_destination(session["user_id"], destination)
                session["last_destination"] = destination

            geocoded = geocode_destination(destination)
            if geocoded is None:
                results = []
            else:
                origin = geocoded
                results = attach_confidence_labels(rank_spots(load_spots_with_distance(geocoded)))
                results = apply_sort(results, preferred_sort)
    elif "user_id" in session and session.get("last_destination"):
        destination = session["last_destination"]

    return render_template(
        "index.html",
        destination=destination,
        results=results,
        error=error,
        origin=origin,
        preferred_sort=preferred_sort,
        run_agent=run_agent,
    )


@app.route("/preferences/sort", methods=["POST"])
def save_sort_preference():
    if "user_id" not in session:
        return jsonify({"ok": True})

    data = request.get_json(silent=True) or {}
    sort_value = data.get("sort")
    if sort_value not in VALID_SORTS:
        return jsonify({"error": "invalid sort value"}), 400

    set_preferred_sort(session["user_id"], sort_value)
    session["preferred_sort"] = sort_value
    return jsonify({"ok": True})


@app.route("/components")
def components():
    return render_template("components.html")


@app.route("/workflows")
def workflows():
    return render_template("workflows.html")


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
            session["role"] = "user"
            session["last_destination"] = None
            session["preferred_sort"] = "best"
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
            session["role"] = user["role"]
            session["last_destination"] = user["last_destination"]
            session["preferred_sort"] = user["preferred_sort"]
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
        sources = rag.retrieve(message)
    except Exception:
        sources = []

    try:
        result = ask_assistant(message, model=model, sources=sources)
    except RuntimeError:
        return jsonify({"reply": "The Spotta Assistant isn't configured yet. Ask the site owner to add an OpenRouter API key.", "sources": []})
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        return jsonify({"reply": f"The assistant couldn't reach that model (error {status}). Try the free model, or check that model has OpenRouter credits.", "sources": []})
    except requests.exceptions.RequestException:
        return jsonify({"reply": "The assistant is temporarily unavailable. Please try again.", "sources": []})
    except (KeyError, IndexError):
        return jsonify({"reply": "The model sent back an unexpected response. Please try again.", "sources": []})

    reply = result["reply"]
    response_sources = sources
    if not can_see_sources():
        reply = strip_citations(reply)
        response_sources = []

    return jsonify({
        "reply": reply,
        "sources": response_sources,
        "model": result["model"],
        "response_time": result["response_time"],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
    })


@app.route("/assistant/rate", methods=["POST"])
def assistant_rate():
    data = request.get_json(silent=True) or {}

    rating = data.get("rating")
    if rating not in ("up", "down"):
        return jsonify({"error": "rating must be 'up' or 'down'"}), 400

    question = (data.get("question") or "").strip()
    response = (data.get("response") or "").strip()
    if not question or not response:
        return jsonify({"error": "question and response are required"}), 400

    entry = {
        "question": question,
        "response": response,
        "rating": rating,
        "model": data.get("model", "unknown"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "response_time_seconds": data.get("response_time"),
        "input_tokens": data.get("input_tokens"),
        "output_tokens": data.get("output_tokens"),
    }

    save_result(entry)

    return jsonify({"ok": True})


@app.route("/assistant/rag-status")
def assistant_rag_status():
    rag.ensure_index_building()
    return jsonify(rag.get_status())


@app.route("/dashboard")
@login_required
def dashboard():
    progress = get_progress_for_user(session["user_id"])
    spots_by_id = {spot["id"]: spot for spot in load_spots()}

    activity = []
    for entry in progress:
        spot = spots_by_id.get(entry["spot_id"])
        activity.append({
            "spot_id": entry["spot_id"],
            "status": entry["status"],
            "updated_at": entry["updated_at"],
            "spot_name": spot["name"] if spot else None,
            "price_per_hour": spot["price_per_hour"] if spot else None,
        })

    unique_spots = len({entry["spot_id"] for entry in activity})

    return render_template(
        "dashboard.html",
        activity=activity,
        visit_count=len(activity),
        unique_spots=unique_spots,
    )


@app.route("/settings", methods=["GET", "POST"])
@admin_required
def settings():
    saved = None

    if request.method == "POST":
        target = request.form.get("target")
        content = request.form.get("content", "")

        if target == "knowledge_base":
            with open(KB_PATH, "w", encoding="utf-8") as f:
                f.write(content)
            rag.rebuild_index_async()
            saved = "knowledge_base"
        elif target == "prompt":
            with open(PROMPT_PATH, "w", encoding="utf-8") as f:
                f.write(content)
            saved = "prompt"

    with open(KB_PATH, encoding="utf-8") as f:
        knowledge_base = f.read()
    with open(PROMPT_PATH, encoding="utf-8") as f:
        prompt = f.read()

    return render_template("settings.html", knowledge_base=knowledge_base, prompt=prompt, saved=saved)


@app.route("/chunks", methods=["GET", "POST"])
@admin_required
def chunks_page():
    if request.method == "POST":
        try:
            chunk_size = int(request.form.get("chunk_size", rag.DEFAULT_CHUNK_SIZE))
        except ValueError:
            chunk_size = rag.DEFAULT_CHUNK_SIZE
        rag.rebuild_index_async(chunk_size)
        return redirect(url_for("chunks_page", building=1))

    building = request.args.get("building") == "1"
    return render_template(
        "chunks.html",
        chunks=rag.get_chunks(),
        chunk_size=rag.get_chunk_size(),
        chunk_sizes=rag.AVAILABLE_CHUNK_SIZES,
        building=building,
    )


@app.route("/results")
@login_required
def results_page():
    results = sorted(load_results(), key=lambda r: r["timestamp"], reverse=True)

    up_count = sum(1 for r in results if r["rating"] == "up")
    down_count = sum(1 for r in results if r["rating"] == "down")
    total = up_count + down_count
    positive_pct = round((up_count / total) * 100, 1) if total else 0

    return render_template(
        "results.html",
        results=results,
        up_count=up_count,
        down_count=down_count,
        positive_pct=positive_pct,
    )


if __name__ == "__main__":
    app.run(debug=True)
