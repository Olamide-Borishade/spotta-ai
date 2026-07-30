# Spotta AI

Spotta AI is a browser-based parking assistant for busy downtown cores, starting
with downtown Vancouver. Drivers waste time, fuel, and patience circling for
parking — Spotta takes a destination and returns a single best-spot
recommendation, no app download required.

This repo is a proof-of-concept prototype of that core flow.

## How it works

1. Enter a destination on the homepage.
2. Spotta ranks a set of nearby parking spots by distance, price, and
   availability confidence, and shows them as a list.
3. Pick a spot to see a mock "Navigate" screen with turn-by-turn directions.

## Running locally

```
pip install -r requirements.txt
python app.py
```


Then open `http://127.0.0.1:5000` in your browser.

## Project structure

app.py - routes and app entrypoint
logic/ranking.py - scoring/ranking logic (rule-based placeholder for AI)
data/spots.json - sample parking spot data
templates/ - HTML pages (Jinja2)
static/ - CSS


## Implemented vs. placeholder

**Implemented:**
- Destination search form
- Ranked results list (distance, price, confidence)
- Mock "Navigate" screen with fake directions

**Placeholders for future work:**
- `logic/ranking.py` uses a simple weighted formula instead of a real
  AI/ML ranking model (see the `TODO` in that file).
- `data/spots.json` is hardcoded sample data instead of a live feed or
  database.
- Navigation is mock text, not real turn-by-turn routing.