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

## Mobile

The whole site (not just the homepage) is built to work on phones without
feeling like a different, cut-down app: same dark theme, same layout logic,
just reflowed. The header nav wraps onto its own row instead of squeezing or
clipping, and the homepage hero/search bar no longer force horizontal
scrolling on narrow screens (a real bug from CSS Grid/Flexbox not shrinking
below their content's natural minimum width, fixed by explicit `minmax(0, ...)`
grid tracks and `min-width: 0` on flex children).

## Voice search

Tapping the mic next to the homepage search box lets you speak a destination
instead of typing it (`static/voice.js`, browser Web Speech API, Chrome/Edge).
Natural phrasing works, not just a bare address: a phrase like "can you find
me a parking spot in downtown Vancouver" is trimmed down to "downtown
Vancouver" before it's geocoded, since Nominatim can't resolve full
conversational sentences. A real address still works and geocodes more
precisely; the trimming only kicks in on the homepage search mic, not the
chatbot's mic, since the chatbot needs the full question verbatim.

## AI model connection

`logic/agents.py` connects to an LLM through [OpenRouter](https://openrouter.ai)
so a model can be called from code, with the provider swappable later.

- Set `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` in a `.env` file (not committed).
- Call `ask_model(message)` to get a reply string. Raises clearly if the key is missing.
- Test with `pytest -s tests/test_agents.py`.

## Spotta Assistant (help chatbot)

A floating chat widget in the bottom-right corner, on every page, answers
questions about how the site works (search, confidence scores, the map,
navigating, accounts, and more).

- Backend: `POST /assistant` retrieves relevant knowledge base chunks (see
  Retrieval-augmented answers below), then calls `ask_assistant(message,
  model, sources)` in `logic/agents.py`. The API key never reaches the browser.
- The widget's model dropdown offers a free default plus two paid OpenRouter
  models, with a link to browse all models. Paid models need OpenRouter
  credits; a clear in-chat message shows if that's missing, no crash.
- If `OPENROUTER_API_KEY` isn't set, the widget still opens and says so
  clearly instead of failing silently.
- After each reply, the server console prints a metrics readout: input/output
  tokens, time taken, and an estimated cost (from a small per-model price
  table in `logic/agents.py`; unmapped models show "cost: n/a").
- Edit `data/knowledge_base.md` and `logic/prompts/website_chatbot.txt` directly
  from the browser at `/settings` (behind login) instead of editing files by hand.

## Retrieval-augmented answers (RAG)

Instead of stuffing the whole knowledge base into every prompt, the assistant
retrieves only the most relevant pieces for each question.

- `data/knowledge_base.md` is split into chunks of about 128 tokens each
  (`logic/rag.py`), keeping bullet points and related lines together rather
  than splitting mid-thought.
- Each chunk is embedded with `sentence-transformers` (`all-MiniLM-L6-v2`) and
  stored, alongside its text, in a local ChromaDB vector store (`data/chroma/`).
- On each question, the question itself is embedded and the top 3 most
  similar chunks are retrieved and passed into the prompt, replacing the old
  `{knowledge_base}` placeholder with a `{context}` one. The model is
  instructed to answer only from that retrieved context.
- The model cites which chunk(s) it used inline, like `[Source 1]`. In the
  chat widget, clicking a citation reveals that chunk's exact text and
  similarity score. Citations are only visible to `admin`/`betatester`
  accounts (see Roles below); everyone else gets a clean answer with no
  `[Source N]` tags and no chunk data in the response at all.
- The first time the index needs to be built (or rebuilt), embedding the
  chunks takes a few seconds; the chat widget shows a "Preparing knowledge
  base…" message instead of appearing frozen, and polls `GET
  /assistant/rag-status` until it's ready.
- `/chunks` (behind login) lists every extracted chunk with its section and
  token count, and lets you pick a different chunk size and re-run chunking
  and embedding from the browser.

## Response ratings

Every real chatbot reply (not error fallbacks) gets a 👍/👎 under it in the
chat widget. Clicking one disables both buttons for that message and posts
to `POST /assistant/rate`, which appends one entry to `data/results.json`
with the question, response, rating, model, timestamp, response time, and
input/output token counts.

- `/results` (behind login) lists every rated response, most recent first,
  with the rating icon, model badge, question, and answer; click a row to
  expand its full details.
- The top of `/results` shows total thumbs up/down and the percent positive.

## Roles

Every account has a `role`: `user` (default on signup), `betatester`, or
`admin`.

- `admin`/`betatester`: see RAG citations in the chatbot (see above).
- `admin` only: `/settings` and `/chunks`, which edit the chatbot's content
  and rebuild the retrieval index. Non-admins get a 403 and don't see the
  nav links at all.
- `/results` and `/dashboard` stay behind plain login, open to any signed-in
  account.
- Promote or demote a user from the command line:
  `python scripts/set_role.py <username> <user|betatester|admin>`
- A role change only takes effect on that user's next login, since the role
  is cached in the session at login/signup time, not re-checked per request.

## Memory

Logged-in accounts get two persisted preferences so returning visits feel
context-aware, stored on the `users` row (`last_destination`, `preferred_sort`):

- The homepage prefills the search box with your last searched destination
  (it doesn't auto-search; you still click Search).
- Your last-used sort order (best match/cheapest/closest/most likely open)
  is remembered and applied to the next search's results automatically,
  including which option the dropdown shows as selected. Changing the sort
  dropdown saves the new preference via `POST /preferences/sort`.
- Anonymous (logged-out) searches aren't remembered.

## Results map

The results map (Leaflet, `#results-map` on the homepage) plots more than
just pins:

- A 1km circle centered on your searched destination shows the search radius
  at a glance, even without reading each spot's distance.
- Each spot's pin is colored to match its confidence badge: green for
  "Likely open", yellow for "Uncertain", red for "Often full" — same colors,
  same meaning, in both the list and the map.
- The destination itself gets a small teal marker in the center of the circle.

## "Find Me Better" agent loop

A "Find Me Better" button next to Driving Mode runs entirely client-side on
the current search results (no new route). It starts from ideal constraints
(within 0.3 km, $2.50/hr or less, 80%+ confidence) and, if nothing in the
current results qualifies, relaxes one constraint at a time (distance, then
price, then confidence, repeating) until a spot matches or it runs out of
relaxation steps, in which case it falls back to the best-ranked spot overall
and says so plainly.

- Highlights the chosen card and scrolls to it, and shows a banner explaining
  what (if anything) had to be relaxed to find it.
- Hidden while Driving Mode is on, same as the sort controls, since Driving
  Mode's simplified view isn't the place for another control.

## Components page

`/components` (open to everyone, no login) is a static status map of Spotta's
architecture: three sections (Data Connectors, Agent/Brain, Tools/Services),
each a row of glass cards styled to match the dark homepage theme. Every card
carries a "live" or "not implemented yet" badge reflecting what's actually
built right now; nothing on the page is wired to real data or functionality.

## Workflows page

`/workflows` (open to everyone, no login) is a catalog of how Spotta's
components combine into end-to-end workflows, styled like `/components`.
Each card names its components and has a real "Run" action, no mocks, all
reusing existing routes and features:

- **Find Parking Near a Destination**: a destination input that submits to
  `/` via `GET ?destination=...`, running the real search/ranking and landing
  on the real results.
- **Ask the Assistant About Parking**: a "Run" button that opens the existing
  Spotta Assistant widget (same trigger as its own launcher button).
- **Find Me a Better Spot**: a destination input that submits to `/` via
  `GET ?destination=...&run_agent=1`; once real results load, the page
  auto-runs the existing client-side Find Me Better agent loop and shows its
  recommended spot and relaxation trail, same as clicking "Find Me Better" by
  hand. There's no separate duration/budget input since the underlying loop
  doesn't take one, only destination.

A `logic/workflows/` package exists as a placeholder for whenever any of
these workflows need real backend logic beyond gluing existing features
together.

## Project structure

app.py - routes and app entrypoint
logic/ranking.py - scoring/ranking logic (rule-based placeholder for AI)
logic/agents.py - OpenRouter LLM connection
logic/rag.py - chunking, embedding, and retrieval for the chatbot
data/spots.json - sample parking spot data
data/knowledge_base.md - chatbot's source facts
scripts/set_role.py - promote/demote a user's role
templates/components.html - /components status catalog (UI only)
templates/workflows.html - /workflows catalog (UI only)
logic/workflows/ - placeholder for future workflow logic
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
