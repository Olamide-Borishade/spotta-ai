# CLAUDE.md

## 🎨 Style
- ✂️ concise, no filler
- 🧼 clean, readable
- 🧾 minimal comments and docs

## ⚙️ Rules
- ⚡ minimal code and libraries
- 🧱 modular, reusable, no repetition
- 🏷️ no hardcoding, use variables
- 🧩 use HTML templates with a base template
- 🚫 no silent fallbacks, fail clearly
- 🚷 no em-dashes at all costs
- 📄 update `requirements.txt` if needed
- 📝 update `CLAUDE.md` on structure changes
- 📘 update `README.md` whenever a new feature is added
- Do not do browser testing (like playwright) unless I explicitly tell you to.

## 🧰 Stack
- 🐍 Flask, SQLite

## 🗂️ Code Structure
- 🚪 **`app.py`** - Flask app entry point, routes
- 🖼️ **`templates/`** - front end (Jinja2)
- 🧩 **`templates/components.html`** - `/components` catalog page listing Spotta's building blocks (live/not implemented yet), UI only
- 🔀 **`templates/workflows.html`** - `/workflows` catalog page, each card runnable: search reuses `/` via a GET `?destination=` query, "agentic" card also passes `?run_agent=1` to auto-run the existing Find Me Better loop, assistant card opens the existing chat widget
- 🎨 **`static/`** - CSS, images, icons, small JS (voice input, scroll-reveal)
- 🗄️ **`data/`** - all app data
- 💾 **`data/app.db`** - user accounts, roles (`user`/`betatester`/`admin`), memory (`last_destination`, `preferred_sort`), and progress (SQLite)
- 📊 **`data/spots.json`** - parking spot data (real City of Vancouver locations/prices; confidence is computed dynamically per request, capped at `MAX_CONFIDENCE` (80%) to stay honest against real live-availability providers, see `logic/ranking.py`)
- 📚 **`data/knowledge_base.md`** - editable facts for the Spotta Assistant chatbot, chunked and embedded for RAG
- 🧠 **`data/chroma/`** - ChromaDB vector store for knowledge base chunks (generated, gitignored, rebuild via `/chunks`)
- 👍 **`data/results.json`** - thumbs up/down ratings on chatbot responses (generated, gitignored, view at `/results`)
- ⚙️ **`logic/`** - backend logic (ranking, geocoding, parknav adapter, OpenRouter agent calls)
- 🔀 **`logic/workflows/`** - placeholder for future workflow logic (see `/workflows` catalog page)
- 🔎 **`logic/rag.py`** - chunking, embedding (sentence-transformers), and retrieval for the chatbot
- 💬 **`logic/prompts/`** - system prompt text files for AI agents (e.g. `website_chatbot.txt`)
- 🧪 **`scripts/`** - quick scripting (e.g. one-off data prep)
- ✅ **`tests/`** - unit tests (pytest)

## 🔀 Planned Migration (not current state, do not assume)

The following are intended future changes, NOT the present setup. Do not build against these until explicitly told the migration has happened:

- `logic/` may later be renamed/restructured to `src/`
- `data/app.db` may later become `data/data.db` synced with Supabase
- Auth may later move from local username/password to GitHub OAuth

## ✅ Final
- 📋 End with the header Summary and 1-3 concise bullet points of what was done under it. Each bullet needs a bold prefix followed by a colon.
- 🎯 End with **"🎯 All Done Amigo"**
