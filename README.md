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

```bash
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000` in your browser.

## Homepage design

The homepage is a single flowing dark page (v3 design): animated hero,
glass-card sections for the problem/how-it-works/live-map-preview/about,
and scroll-reveal on each section. The live map preview under "Live map" is
a decorative static visual, not real data; the actual ranked-results map
(Leaflet) still renders after a real search, restyled to match. Respects
`prefers-reduced-motion`.

## Auth pages design

Login and signup share a blended split-screen layout: a single background
gradient flowing from dark navy into chalk (no hard seam), a branded left
side with an animated radar signature, and a translucent frosted-glass form
card on the right. Collapses to the form only on narrow screens. Respects
`prefers-reduced-motion`.

## AI model connection

`logic/agents.py` connects to an LLM through [OpenRouter](https://openrouter.ai)
so a model can be called from code, with the provider swappable later.

- Set `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` in a `.env` file (not committed).
- Call `ask_model(message)` to get a reply string. Raises clearly if the key is missing.
- Test with `pytest -s tests/test_agents.py`.

## Spotta Assistant (help chatbot)

A floating chat widget in the bottom-right corner, on every page, answers
questions about how the site works (search, confidence scores, the map,
navigating, accounts). It answers from a fixed system prompt in
`logic/prompts/website_chatbot.txt`, no lookups needed.

- Backend: `POST /assistant` calls `ask_assistant(message, model)` in
  `logic/agents.py`. The API key never reaches the browser.
- The widget's model dropdown offers a free default plus two paid OpenRouter
  models, with a link to browse all models. Paid models need OpenRouter
  credits; a clear in-chat message shows if that's missing, no crash.
- If `OPENROUTER_API_KEY` isn't set, the widget still opens and says so
  clearly instead of failing silently.
- Facts live in `data/knowledge_base.md`, separate from the prompt file.
  Edit that file to change what the assistant knows, no code change needed.
  The prompt (`logic/prompts/website_chatbot.txt`) holds only the role and
  behavior rules, with a `{knowledge_base}` placeholder swapped in at request
  time.
- After each reply, the server console prints a metrics readout: input/output
  tokens, time taken, and an estimated cost (from a small per-model price
  table in `logic/agents.py`; unmapped models show "cost: n/a").

## Project structure

app.py - routes and app entrypoint
logic/ranking.py - scoring/ranking logic (rule-based placeholder for AI)
logic/agents.py - OpenRouter LLM connection
data/spots.json - sample parking spot data
templates/ - HTML pages (Jinja2)
static/ - CSS, icons, small JS (voice input, scroll-reveal)
tests/ - unit tests (pytest)

## Implemented vs. placeholder

**Implemented:**

- Destination search form, with tap-to-talk voice input (browser Web Speech API, Chrome/Edge)
- Ranked results list (distance, price, confidence)
- Mock "Navigate" screen with fake directions
- LLM connection via OpenRouter (`logic/agents.py`), not yet wired into a user-facing feature

**Placeholders for future work:**

- `logic/ranking.py` uses a simple weighted formula instead of a real
  AI/ML ranking model (see the `TODO` in that file).
- `data/spots.json` is hardcoded sample data instead of a live feed or
  database.
- Navigation is mock text, not real turn-by-turn routing.
